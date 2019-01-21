# aws-dart - A companion for aws-vault #
When you're a global company with a few IAM roles in a bunch of regions and specifying the region manually every time is tedious.

## Requirements ##
* [aws-vault](https://github.com/99designs/aws-vault)
* `pip install -r requirements.txt`

## Usage ##
In your `~/.aws/config` file, add some **target**s. These allow you to specify the config settings you wish to override while inheriting the rest from the profile it references.

Each **target** entry must contain a **profile** key that contains the name of a defined profile.

```ini
# This profile is what references your credentials in aws-vault
[profile id]
mfa_serial = arn:aws:iam::123456789012:mfa/user

# This profile is what you normally pass to aws-vault
[profile dev]
source_profile = id
role_arn = arn:aws:iam:...
mfa_serial = arn:aws:iam::123456789012:mfa/user

# This is what you will pass to aws-dart
[target dev-us]
profile = dev
region = us-east-1
```

Run the command such as `aws-dart exec dev-us env | grep AWS_REGION`

It will run `aws-vault exec dev env | grep AWS_REGION` but your grep will result in `AWS_REGION=us-east-1` instead of nothing.

## How it works ##
This generates a new config file containing your **defaults** header and a profile that combines the target with its **profile**. Then it sets the `AWS_CONFIG_FILE` environment variable before running the aws-vault command.

The new config is written to the same location as the last one but with the target name appended. So if you're using the default location, `~/.aws/config`, it would write to `~/.aws/config_dev-us`

Thus all target names should be filename safe. (It's not like you wanted to quote the argument on the CLI anyway, right?)

## Installation ##
Download this and link the `aws-dart.py` file somewhere in a folder in your $PATH

On linux I have a user-level bin folder in my $PATH at `~/.local/bin` so I linked it in there with `ln -s ~/src/aws-dart/aws-dart.py ~/.local/bin/aws-dart`
