import json
import os
import shutil
import git
from pathlib import Path
from typing import Dict, List, Tuple


class GistToRepoSync:
    def __init__(self):
        self.gist_id = os.environ['INPUT_GIST_ID']
        self.token = os.environ['INPUT_GIST_TOKEN']
        self.mapping_strategy = os.environ.get('INPUT_MAPPING_STRATEGY', 'same_names')
        self.file_mappings = json.loads(os.environ.get('INPUT_FILE_MAPPINGS', '{}'))
        self.target_path = os.environ.get('INPUT_TARGET_PATH', './')
        self.file_prefix = os.environ.get('INPUT_FILE_PREFIX', '')
        self.merge_strategy = os.environ.get('INPUT_MERGE_STRATEGY', 'overwrite')
        self.create_pr = os.environ.get('INPUT_CREATE_PR', 'false').lower() == 'true'
        self.commit_message = os.environ.get('INPUT_COMMIT_MESSAGE', 'Sync from Gist {gist_id}')
        self.git_user_name = os.environ.get('INPUT_GIT_USER_NAME', 'github-actions[bot]')
        self.git_user_email = os.environ.get('INPUT_GIT_USER_EMAIL', 'github-actions[bot]@users.noreply.github.com')
        
        self.gist_git_url = f'https://{self.token}@gist.github.com/{self.gist_id}.git'
        self.gist_clone_dir = f'gist-clone-temp/{self.gist_id}'
        self.repo_root = os.environ.get('GITHUB_WORKSPACE', '.')

    def prepare_gist_clone_dir(self):
        """Clean and prepare directory for gist clone"""
        if os.path.exists(self.gist_clone_dir):
            shutil.rmtree(self.gist_clone_dir)
        os.makedirs(os.path.dirname(self.gist_clone_dir), exist_ok=True)

    def clone_gist(self):
        """Clone the gist repository"""
        print(f'Cloning Gist {self.gist_id}...')
        try:
            git.Repo.clone_from(self.gist_git_url, self.gist_clone_dir, depth=1)
            print('Gist cloned successfully')
        except Exception as e:
            raise ValueError(f'Unable to clone gist: {str(e)}')

    def get_gist_files(self) -> List[str]:
        """Get list of files from cloned gist, excluding .git directory"""
        files = os.listdir(self.gist_clone_dir)
        if '.git' in files:
            files.remove('.git')
        print(f'Found {len(files)} files in Gist: {files}')
        return files

    def build_file_map(self, gist_files: List[str]) -> Dict[str, str]:
        """
        Build mapping from gist files to repo paths based on strategy
        Returns: {gist_file: repo_relative_path}
        """
        file_map = {}
        
        if self.mapping_strategy == 'explicit':
            # Use provided explicit mappings
            for gist_file in gist_files:
                if gist_file in self.file_mappings:
                    file_map[gist_file] = self.file_mappings[gist_file]
                else:
                    print(f'Warning: No mapping found for {gist_file}, skipping')
        
        elif self.mapping_strategy == 'same_names':
            # Map to same filename in target directory
            for gist_file in gist_files:
                target_file = os.path.join(self.target_path, gist_file)
                file_map[gist_file] = target_file
        
        elif self.mapping_strategy == 'prefix':
            # Add/remove prefix from filenames
            for gist_file in gist_files:
                if self.file_prefix and gist_file.startswith(self.file_prefix):
                    # Remove prefix
                    new_name = gist_file[len(self.file_prefix):]
                else:
                    # Add prefix
                    new_name = f'{self.file_prefix}{gist_file}'
                target_file = os.path.join(self.target_path, new_name)
                file_map[gist_file] = target_file
        
        elif self.mapping_strategy == 'all_to_directory':
            # All files go to target directory with same names
            for gist_file in gist_files:
                target_file = os.path.join(self.target_path, gist_file)
                file_map[gist_file] = target_file
        
        else:
            raise ValueError(f'Unknown mapping strategy: {self.mapping_strategy}')
        
        print(f'File mapping strategy "{self.mapping_strategy}" created {len(file_map)} mappings')
        for gist_file, repo_path in file_map.items():
            print(f'  {gist_file} -> {repo_path}')
        
        return file_map

    def should_copy_file(self, target_path: str) -> Tuple[bool, str]:
        """
        Determine if file should be copied based on merge strategy
        Returns: (should_copy, reason)
        """
        if self.merge_strategy == 'overwrite':
            return True, 'overwrite strategy'
        
        elif self.merge_strategy == 'skip_existing':
            if os.path.exists(target_path):
                return False, 'file exists and skip_existing strategy'
            return True, 'file does not exist'
        
        elif self.merge_strategy == 'newer_only':
            # Future feature: compare timestamps
            print('Warning: "newer_only" strategy not yet implemented, using overwrite')
            return True, 'overwrite (newer_only not implemented)'
        
        else:
            print(f'Warning: Unknown merge strategy "{self.merge_strategy}", using overwrite')
            return True, 'overwrite (unknown strategy)'

    def sync_files(self, file_map: Dict[str, str]) -> List[str]:
        """
        Copy files from gist to repo according to file map
        Returns: list of files that were modified
        """
        modified_files = []
        skipped_files = []
        
        for gist_file, repo_relative_path in file_map.items():
            gist_source = os.path.join(self.gist_clone_dir, gist_file)
            repo_target = os.path.join(self.repo_root, repo_relative_path)
            
            # Create target directory if needed
            os.makedirs(os.path.dirname(repo_target), exist_ok=True)
            
            # Check merge strategy
            should_copy, reason = self.should_copy_file(repo_target)
            
            if should_copy:
                shutil.copy2(gist_source, repo_target)
                modified_files.append(repo_relative_path)
                print(f'Copied: {gist_file} -> {repo_relative_path} ({reason})')
            else:
                skipped_files.append(repo_relative_path)
                print(f'Skipped: {gist_file} -> {repo_relative_path} ({reason})')
        
        print(f'\nSummary: {len(modified_files)} files copied, {len(skipped_files)} files skipped')
        return modified_files

    def commit_changes(self, modified_files: List[str]):
        """Commit changes to the repository"""
        repo = git.Repo(self.repo_root)
        
        # Configure git user
        with repo.config_writer() as git_config:
            git_config.set_value('user', 'name', self.git_user_name)
            git_config.set_value('user', 'email', self.git_user_email)
        
        # Stage modified files
        repo.index.add(modified_files)
        
        # Check if there are actual changes
        if not repo.is_dirty():
            print('No changes detected, nothing to commit')
            return False
        
        # Format commit message
        commit_msg = self.commit_message.format(
            gist_id=self.gist_id,
            actor=os.environ.get('GITHUB_ACTOR', 'unknown'),
            ref=os.environ.get('GITHUB_REF', 'unknown')
        )
        
        # Commit
        repo.index.commit(commit_msg)
        print(f'Committed changes: {commit_msg}')
        
        # Push
        origin = repo.remote('origin')
        origin.push()
        print('Pushed changes to repository')
        
        return True

    def create_pull_request(self, modified_files: List[str]):
        """Create a pull request (future feature)"""
        print('Pull request creation not yet implemented')
        print('Modified files:', modified_files)
        # Future: Use GitHub API to create PR
        raise NotImplementedError('Pull request creation is a future feature')

    def run(self):
        """Main execution flow"""
        print(f'=== Gist to Repo Sync ===')
        print(f'Gist ID: {self.gist_id}')
        print(f'Mapping Strategy: {self.mapping_strategy}')
        print(f'Merge Strategy: {self.merge_strategy}')
        print(f'Target Path: {self.target_path}')
        print(f'Create PR: {self.create_pr}')
        print()
        
        try:
            # Step 1: Prepare and clone gist
            self.prepare_gist_clone_dir()
            self.clone_gist()
            
            # Step 2: Get files from gist
            gist_files = self.get_gist_files()
            
            if not gist_files:
                print('No files found in Gist, exiting')
                return
            
            # Step 3: Build file mapping
            file_map = self.build_file_map(gist_files)
            
            if not file_map:
                print('No files to sync after mapping, exiting')
                return
            
            # Step 4: Sync files
            modified_files = self.sync_files(file_map)
            
            if not modified_files:
                print('No files were modified, exiting')
                return
            
            # Step 5: Commit or create PR
            if self.create_pr:
                self.create_pull_request(modified_files)
            else:
                committed = self.commit_changes(modified_files)
                if committed:
                    print('\n✓ Sync completed successfully!')
                else:
                    print('\n✓ Sync completed (no changes to commit)')
        
        except Exception as e:
            print(f'\n✗ Error: {str(e)}')
            raise
        
        finally:
            # Cleanup
            if os.path.exists(self.gist_clone_dir):
                shutil.rmtree(self.gist_clone_dir)
                print('\nCleaned up temporary files')


if __name__ == '__main__':
    syncer = GistToRepoSync()
    syncer.run()