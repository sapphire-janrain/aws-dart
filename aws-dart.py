#!/usr/bin/env python3
# MIT Licensed #

import os
import sys
import subprocess
from botocore import configloader, exceptions


def parse_aws_config(filename="~/.aws/config"):
    real_filename = os.path.expanduser(filename)
    return configloader.load_config(real_filename)


def load_target(config, target_name):
    key = "target {}".format(target_name)
    if key in config:
        target = config[key]
        if "profile" not in target:
            raise exceptions.MissingParametersError(object_name=target_name, missing="profile")

        profile_name = target.pop("profile")
        if profile_name not in config["profiles"]:
            raise exceptions.ProfileNotFound(profile_name)

        profile = config["profiles"][profile_name]
        profile_key = "profile {}".format(profile_name)
        temporary_config = profile.copy()
        temporary_config.update(target)
        temporary_config = { profile_key: temporary_config }

        if "default" in config["profiles"]:
            temporary_config["default"] = config["profiles"]["default"]

        return profile_name, temporary_config


def write_config(filename, temporary_config):
    real_filename = os.path.expanduser(filename)
    with open(real_filename, "w") as f:
        for section_name, section in temporary_config.items():
            print("[{}]".format(section_name), file=f)

            for key, value in section.items():
                if isinstance(value, dict):
                    print("{} =".format(key), file=f)

                    for dkey, dvalue in value.items():
                        print("  {} = {}".format(dkey, dvalue), file=f)
                else:
                    print("{} = {}".format(key, value), file=f)


def run_vault_with_config(profile, filename):
    real_filename = os.path.expanduser(filename)
    env = os.environ.copy()
    env["AWS_CONFIG_FILE"] = real_filename
    result = subprocess.run(("aws-vault", sys.argv[1], profile, *sys.argv[3:]), env=env)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] in ("help", "--help", "-h", "-?", "/?"):
        print(
            "Usage: aws-dart COMMAND TARGET [args]",
            "",
            "  COMMAND - For commands see aws-vault --help",
            "  TARGET  - Target as defined in your ~/.aws/config",
            sep="\n",
        )
        sys.exit(0)

    if len(sys.argv) < 3:
        print("Usage: aws-dart COMMAND TARGET [args]", file=sys.stderr)
        sys.exit(1)

    config_file = os.getenv("AWS_CONFIG_FILE", "~/.aws/config")
    config = parse_aws_config(config_file)

    target_name = sys.argv[2]
    profile, temporary_config = load_target(config, target_name)

    filename = "{}_{}".format(config_file, target_name)
    write_config(filename, temporary_config)

    sys.exit(run_vault_with_config(profile, filename))
