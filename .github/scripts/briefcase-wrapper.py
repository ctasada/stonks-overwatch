#!/usr/bin/env python3
"""
Briefcase wrapper for Docker-in-Docker compatibility.

This script patches Briefcase's Docker integration to work correctly
in Docker-in-Docker scenarios (like when running with 'act').
"""

import os
import sys


def patch_briefcase_docker():
    """Patch Briefcase Docker integration for DinD compatibility."""
    # Monkey-patch the Docker user mapping detection
    try:
        from briefcase.integrations import docker

        original_is_user_mapping_enabled = docker.Docker._is_user_mapping_enabled

        def patched_is_user_mapping_enabled(self, image_tag):
            """
            Patched version that handles Docker-in-Docker scenarios.

            In DinD with act, volume mounts don't work correctly for user mapping detection,
            so we skip the check and return False (no user mapping).
            """
            # Check if we're running under act
            if os.environ.get("ACT"):
                print(">>> Docker-in-Docker detected (act) - skipping user mapping detection")
                return False

            # Check if environment variable is set to disable detection
            if os.environ.get("BRIEFCASE_DOCKER_DISABLE_USER_ID_DETECTION") == "1":
                print(">>> User mapping detection disabled via environment variable")
                return False

            # Otherwise, use original implementation
            try:
                return original_is_user_mapping_enabled(self, image_tag)
            except (FileNotFoundError, OSError) as e:
                # If the original check fails (like in DinD), assume no user mapping
                print(f">>> User mapping detection failed: {e}")
                print(">>> Assuming no user mapping")
                return False

        # Apply the patch
        docker.Docker._is_user_mapping_enabled = patched_is_user_mapping_enabled
        print(">>> Successfully patched Briefcase Docker integration for DinD compatibility")

    except ImportError as e:
        print(f">>> Warning: Could not patch Briefcase: {e}")
        print(">>> Continuing anyway...")


def main():
    """Main entry point - patch Briefcase and run the command."""
    # Apply the patch before importing briefcase's main
    patch_briefcase_docker()

    # Now run briefcase with the original arguments
    try:
        from briefcase.__main__ import main as briefcase_main

        sys.exit(briefcase_main())
    except Exception as e:
        print(f">>> Error running Briefcase: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
