#!/usr/bin/env python3
# MIT Licensed #

import os
import sys
import subprocess
from collections import OrderedDict

from botocore import configloader, exceptions


def parse_aws_config(filename="~/.aws/config"):
    real_filename = os.path.expanduser(filename)
    return configloader.load_config(real_filename)


def load_target(config, target_name):
    target_key = None
    for key in config.keys():
        if key.startswith("target "):
            targets = key[7:].split()
            if target_name in targets:
                target_key = key
                fn_key = targets[0]
                break

    if target_key is not None:
        target = config[target_key]
        if "profile" not in target:
            raise exceptions.MissingParametersError(object_name=target_name, missing="profile")

        profile_name = target.pop("profile")
        if profile_name not in config["profiles"]:
            raise exceptions.ProfileNotFound(profile=profile_name)

        temporary_config = OrderedDict()

        if "default" in config["profiles"]:
            temporary_config["default"] = config["profiles"]["default"]

        profile = config["profiles"][profile_name]
        if "source_profile" in profile:
            source_profile_name = profile["source_profile"]
            if source_profile_name not in config["profiles"]:
                raise exceptions.ProfileNotFound(source_profile_name)

            source_profile_key = "profile {}".format(source_profile_name)
            temporary_config[source_profile_key] = config["profiles"][source_profile_name]

        profile_copy = profile.copy()
        profile_copy.update(target)
        profile_key = "profile {}".format(profile_name)
        temporary_config[profile_key] = profile_copy

        return profile_name, fn_key, temporary_config
    else:
        raise exceptions.ProfileNotFound(profile=key)


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
    profile, real_target_name, temporary_config = load_target(config, target_name)

    filename = "{}_{}".format(config_file, real_target_name)
    write_config(filename, temporary_config)

    sys.exit(run_vault_with_config(profile, filename))
