#!/usr/bin/env python3
"""
    This script handles installing system dependencies for games using the
    Steam runtime.  It is intended to be customized by other distributions
    to "do the right thing"

    Usage: steamdeps dependencies.txt
"""

import argparse
import glob
import logging
import os
import re
import shlex
import subprocess
import sys

from steam_launcher.launcherutils import run_subprocess

try:
    from shlex import quote
except ImportError:
    # Python 3.2 (not really supported but let's not deliberately break it)
    from pipes import quote

try:
    import typing
except ImportError:
    pass

try:
    import apt
    from aptsources.sourceslist import SourceEntry
except ImportError:
    sys.stderr.write("Couldn't import apt, please install python3-apt or "
                     "update steamdeps for your distribution.\n")
    sys.exit(3)


logger = logging.getLogger('steamdeps')

# This is the set of supported Steam runtime environments
SUPPORTED_STEAM_RUNTIME = ['1']

# This is the set of supported dependency formats
SUPPORTED_STEAM_DEPENDENCY_VERSION = ['1']

# Environment variables that need to be passed through when we re-exec
# under pkexec
PASS_THROUGH_ENV_VARS = (
    'SL_TEST_NVIDIA_VERSION',
    'STEAM_LAUNCHER_VERBOSE',
    'XDG_CURRENT_DESKTOP',
)

_arch = None
_foreign_architectures = None


class OsRelease:
    def __init__(self):
        # type: () -> None
        self._load_any()
        self._is_like = self._data.get('ID_LIKE', '').split()

    def _load_any(self):
        # type: () -> None
        for path in ('/etc/os-release', '/usr/lib/os-release'):
            self._data = self._load(path)

            if self._data:
                return

    def _load(
        self,
        path        # type: str
    ):
        # type: (...) -> typing.Dict[str, str]

        data = {}       # type: typing.Dict[str, str]

        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as reader:
                for line in reader:
                    try:
                        line = line.strip()

                        if not line or line.startswith('#'):
                            continue

                        key, value = line.split('=', 1)

                        data[key] = ''.join(shlex.split(value))

                    except Exception as e:
                        print(
                            'Warning: error parsing %s: line %r: %s'
                            % (path, line, e),
                            file=sys.stderr
                        )
                        continue
        except OSError:
            return {}
        else:
            return data

    def is_os(self, os_id):
        # type: (str) -> bool
        if self._data.get('ID') == os_id:
            return True

        return os_id in self._is_like

    def dump(self):
        print(self._data, file=sys.stderr)


#
# Get the current package architecture
# This may be different than the actual architecture for the case of i386
# chroot environments on amd64 hosts.
#
def get_arch():
    """
    Get the current architecture
    """
    global _arch

    if _arch is None:
        _arch = subprocess.check_output(
            ['dpkg', '--print-architecture']).decode("utf-8").strip()
    return _arch


def get_foreign_architectures():
    """
    Get the enabled foreign architectures
    """
    global _foreign_architectures

    if _foreign_architectures is None:
        _foreign_architectures = subprocess.check_output(
            ['dpkg', '--print-foreign-architectures'],
            universal_newlines=True,
        ).splitlines()
    return _foreign_architectures


# N.B. Version checks are not supported on virtual packages
#
def is_provided(pkgname):
    """
    Check to see if another package Provides this package
    """
    cache = apt.Cache()
    pkgs = cache.get_providing_packages(pkgname)
    for pkg in pkgs:
        if pkg.is_installed:
            return True
    return False


###
class Package:
    """
    Package definition class
    """

    def __init__(self, name, version_conditions):
        self.name = name
        self.version_conditions = version_conditions
        self.installed = None

    def set_installed(self, version):
        self.installed = version

    def is_available(self):
        if self.installed is None:
            # check to see if another package is providing this virtual package
            return is_provided(self.name)

        for (op, version) in self.version_conditions:
            if subprocess.call(['dpkg', '--compare-versions', self.installed,
                                op, version]) != 0:
                return False

        return True

    def __str__(self):
        text = self.name
        for (op, version) in self.version_conditions:
            text += " (%s %s)" % (op, version)
        return text


def is_glvnd():
    try:
        with subprocess.Popen(['apt-cache', 'pkgnames', 'libgl1'],
                              stdout=subprocess.PIPE,) as process:
            for line in process.stdout:
                line = line.decode('utf-8').strip()

                if line == 'libgl1':
                    return True
            return False
    except (OSError, FileNotFoundError):
        return False


def is_package_available(package_name):
    try:
        apt_output = subprocess.check_output(
            ['apt-cache', '-q', 'show', package_name])
        # On SteamOS "xdg-desktop-portal-gtk" is recommended by the backported
        # version of flatpak, even if it is not available in the repositories.
        # For this reason we also check the apt-cache -q show output before
        # asserting that a package is really available.
        return bool(apt_output)
    except (OSError, FileNotFoundError, subprocess.CalledProcessError):
        return False


def choose_xdg_portal_backend(default_backend="xdg-desktop-portal-gtk"):
    gtk_desktop = ["Cinnamon", "GNOME", "LXDE", "MATE", "Unity", "XFCE"]
    kde_desktop = ["KDE"]
    gtk_backend = "xdg-desktop-portal-gtk"
    kde_backend = "xdg-desktop-portal-kde"

    current_desktops = os.environ.get("XDG_CURRENT_DESKTOP", "").split(":")

    for c in current_desktops:
        if c in gtk_desktop:
            if is_package_available(gtk_backend):
                return gtk_backend
        elif c in kde_desktop:
            if is_package_available(kde_backend):
                return kde_backend

    if is_package_available(default_backend):
        return default_backend
    else:
        sys.stderr.write(
            "There isn't a known XDG portal backend that can be installed\n")
        return None


def expected_nvidia_packages():
    # type: (...) -> typing.Dict[str, Package]
    # Returns a map like:
    # {"nvidia-driver-libs:amd64": Package("nvidia-driver-libs:amd64", [])}
    nvidia_packages_to_check = {}       # type: typing.Dict[str, Package]
    nvidia_packages_to_expect = {}      # type: typing.Dict[str, Package]

    if get_arch() != 'amd64':
        return nvidia_packages_to_expect

    try:
        nvidia_version = os.environ.get("SL_TEST_NVIDIA_VERSION")
        if not nvidia_version:
            with open('/sys/module/nvidia/version') as f:
                nvidia_version = f.read()
        nvidia_major_version = nvidia_version.split('.')[0]
    except OSError:
        # If the Nvidia module is not loaded, it's safe to assume that the
        # Nvidia drivers are not in use. No need to install anything else.
        return nvidia_packages_to_expect

    for name in (
        # Debian packages
        "nvidia-driver-libs:amd64",
        "nvidia-legacy-{}xx-driver-libs:amd64".format(nvidia_major_version),
        "nvidia-tesla-{}-driver-libs:amd64".format(nvidia_major_version),
        "nvidia-alternative",
        "nvidia-legacy-{}xx-alternative".format(nvidia_major_version),
        "nvidia-tesla-{}-alternative".format(nvidia_major_version),

        # Ubuntu 18.04+ packages
        "libnvidia-gl-{}:amd64".format(nvidia_major_version),
        "libnvidia-gl-{}-server:amd64".format(nvidia_major_version),
    ):
        nvidia_packages_to_check[name] = Package(name, [])

    update_installed_packages(nvidia_packages_to_check)

    for pkg_name in nvidia_packages_to_check:
        if nvidia_packages_to_check[pkg_name].installed:
            if pkg_name.endswith("-alternative"):
                # If we have a Nvidia kernel module and the "*-alternative"
                # package is installed, we want to ensure that the related
                # user-space "*-driver-libs" are also installed, in both
                # amd64 and i386 architectures
                driver_libs = pkg_name.replace("-alternative", "-driver-libs")
                nvidia_packages_to_expect[driver_libs + ":amd64"] = Package(
                    driver_libs + ":amd64", []
                )
                nvidia_packages_to_expect[driver_libs + ":i386"] = Package(
                    driver_libs + ":i386", []
                )
            else:
                # Ensure that the i386 variant is installed too
                assert pkg_name.endswith(":amd64")
                name_i386 = pkg_name.replace(":amd64", ":i386")
                nvidia_packages_to_expect[name_i386] = Package(name_i386, [])

    if len(nvidia_packages_to_expect) == 0:
        print("Unable to determine whether the expected Nvidia drivers "
              "are available.")
        print("The Steam client may have limited functionality.")

    return nvidia_packages_to_expect


def remap_package(name):
    if name in (
            'python-apt',
    ):
        # Steam claims it needs python-apt, but it doesn't really
        return None

    # Ubuntu 12.04.2, 12.04.3, and 12.04.4 introduce new X stacks which require
    # different sets of incompatible glx packages depending on which X
    # is currently installed.

    cache = apt.Cache()
    for lts in ('quantal', 'raring', 'saucy', 'trusty', 'xenial'):
        xserver = 'xserver-xorg-core-lts-' + lts
        if xserver in cache and cache[xserver].is_installed:
            if name in (
                    'libegl1-mesa',
                    'libgbm1',
                    'libgl1-mesa-glx',
                    'libgl1-mesa-dri',
            ):
                return name + '-lts-' + lts

            if name in (
                    'libegl1',
            ):
                return name + '-mesa-lts-' + lts

    if name in ('libegl1', 'libegl1-mesa'):
        if is_glvnd():
            return 'libegl1'
        else:
            return 'libegl1-mesa'

    if name == 'libgl1-mesa-glx':
        if is_glvnd():
            return 'libgl1'

    return name


###
def create_package(description):
    """
    Create a package object based on a description.
    This can return None if the package isn't meaningful on this platform.
    """
    # Look for architecture conditions, e.g. foo [i386]
    match = re.match(r"(.*) \[([^\]]+)\]", description)
    if match is not None:
        description = match.group(1).strip()
        condition = match.group(2)
        if condition[0] == '!':
            if get_arch() == condition[1:]:
                return None
        else:
            if get_arch() != condition:
                return None

    # Look for version requirements, e.g. foo (>= 1.0)
    version_conditions = []
    while True:
        match = re.search(r"\s*\(\s*([<>=]+)\s*([\w\-.:]+)\s*\)\s*",
                          description)
        if match is None:
            break

        version_conditions.append((match.group(1), match.group(2)))
        description = description[:match.start()] + description[match.end():]

    description = description.strip()

    if ':' in description:
        name, multiarch = description.rsplit(':', 1)
    else:
        name = description
        multiarch = None

    name = remap_package(name)

    if name in (
            "xdg-desktop-portal-gtk",
            "xdg-desktop-portal-kde",
    ):
        name = choose_xdg_portal_backend(name)
        # Skip version conditions for portal backends because we don't know
        # in advance which backend we will need to install.
        # In the future, if necessary, we can enhance this check and, for
        # example, embed a minimum version for each possible backed.
        version_conditions = []

    if name is None:
        return None
    elif multiarch is not None:
        description = name + ':' + multiarch
    else:
        description = name

    return Package(description, version_conditions)


###
def get_terminal(
    title       # type: str
):
    # type: (...) -> typing.List[str]
    """
    Function to find a useful terminal like xterm or compatible
    """
    if "DISPLAY" in os.environ:
        gnome_wait_option = None
        try:
            # Use the new '--wait' option if available
            terminal_out = subprocess.check_output(
                ["gnome-terminal", "--help-terminal-options"]).decode("utf-8")
            if "--wait" in terminal_out:
                gnome_wait_option = "--wait"
            else:
                # If the old '--disable-factory' is supported we use it
                terminal_out = subprocess.check_output(
                    ["gnome-terminal", "--help"]).decode("utf-8")
                if "--disable-factory" in terminal_out:
                    gnome_wait_option = "--disable-factory"

            if gnome_wait_option is not None:
                # If 'gnome-terminal' with the right options is available, we
                # just use it
                return ["gnome-terminal", gnome_wait_option, "-t", title, "--"]
        except FileNotFoundError:
            pass

        programs = [
            ("konsole",
             ["konsole", "--nofork", "-p", "tabtitle=" + title, "-e"]),
            ("xterm",
             ["xterm", "-bg", "#383635", "-fg", "#d1cfcd", "-T", title, "-e"]),
            ("x-terminal-emulator",
             ["x-terminal-emulator", "-T", title, "-e"]),
            # If we reach this point either 'gnome-terminal' is not available
            # or the current version is too old for the new '--wait' option.
            # Anyway we can't know for sure if '--disable-factory' option
            # is supported until we try it because, for example,
            # on Ubuntu 16.04 '--disable-factory' is available but it doesn't
            # show up with '--help'. Leave this 'gnome-terminal' test as the
            # last resort because it's highly likely to fail.
            ("gnome-terminal",
             ["gnome-terminal", "--disable-factory", "-t", title, "--"]),
        ]
        for (program, commandLine) in programs:
            if subprocess.call(['which', program],
                               stdout=subprocess.PIPE) == 0:
                return commandLine

    # Fallback if no GUI terminal program is available
    return ['/usr/bin/env']


def get_terminal_wait(
    title       # type: str
):
    # type: (...) -> typing.List[str]
    return get_terminal(title) + [
        '/bin/sh', '-euc',
        ('e=0; "$@" || e=$?;'
         'printf \'\\nPress return to continue: \'; read line;'
         'exit "$e"'),
        'sh',
    ]


###
def is_root():
    return os.getuid() == 0


###
def is_apt_out_of_sync():
    """
    Returns True if the apt policies are not in sync with what is listed
    in the apt sources lists.
    """
    # We only care about the Steam repository
    steam_uri = 'https://repo.steampowered.com/steam'

    cp = run_subprocess(
        ['apt-cache', 'policy'],
        capture_output=True,
        universal_newlines=True,
    )
    if steam_uri in cp.stdout:
        # The Steam repository is already in the apt policies, no need
        # to update apt sources
        return False

    # Technically, as explained in sources.list(5), also '.sources' files
    # with the deb822 style are understood by apt but they cannot be
    # parsed with python-apt. By default we expect to have the Steam
    # repository in a '.list' file, so it should be safe to skip them.
    # However if we decide to also parse the '.sources' files, we should
    # probably use the python3-debian package.
    sources_list = glob.glob('/etc/apt/sources.list.d/*.list')
    sources_list.append('/etc/apt/sources.list')

    for source in sources_list:
        try:
            with open(source) as f:
                for line in f.readlines():
                    entry = SourceEntry(line, f.name)
                    entry.parse(line)
                    if steam_uri in entry.uri and not entry.disabled:
                        # The Steam repository is in the sources list but not
                        # in the apt policies. We need to update apt sources
                        return True
        except OSError as err:
            print('Failed to open "{}": {}'.format(source, err))

    # Apparently we don't have the Steam repository, no need to update
    # apt sources
    return False


###
def update_apt(show_progress=True):
    logger.debug('Running apt-get update...')

    if show_progress:
        stdout_dest = subprocess.PIPE
    else:
        stdout_dest = subprocess.DEVNULL

    proc = subprocess.Popen(
        ['apt-get', 'update'],
        stdout=stdout_dest,
        bufsize=1,
        universal_newlines=True,
    )
    if show_progress:
        for _ in proc.stdout:
            print('.', end='', flush=True)
        print('')


def needs_i386():
    # type: () -> bool
    return (get_arch() == 'amd64'
            and 'i386' not in get_foreign_architectures())


def enable_i386():
    # type: () -> bool

    global _foreign_architectures

    if needs_i386():
        # Check to make sure 64-bit systems can get 32-bit packages
        logger.debug('Adding i386 architecture...')
        cp = run_subprocess(['dpkg', '--add-architecture', 'i386'])
        if cp.returncode != 0:
            logger.warning(
                'An error occurred while enabling 32-bit (i386) packages',
            )
            return False

    # invalidate cache
    _foreign_architectures = None

    return True


def pass_through_environ(
    argv,       # type: typing.List[str]
):
    # type: (...) -> None

    for var in PASS_THROUGH_ENV_VARS:
        if var in os.environ:
            argv.append('--setenv={}={}'.format(var, os.environ[var]))


###
def update_packages(packages, install_confirmation=True):
    """
    Function to install or update package dependencies, expected to be executed
    in an interactive terminal.
    Ideally we would call some sort of system UI that users were familiar with
    to do this, but nothing that exists yet does what we need.
    """

    if install_confirmation:
        print('\nSteam needs to install these additional packages:')
        print(*packages)
        input('\nPress return to proceed with the installation: ')
    else:
        logger.debug('Will install packages: %s', ' '.join(packages))

    if not is_root():
        # We don't have root privileges, call again this script with pkexec
        logger.debug('Re-running steamdeps as root...')
        argv = [
            'pkexec',
            os.path.abspath(__file__),
            '--interactive',
            # We already showed the confirmation once, no need to repeat it
            '--no-install-confirmation',
            '--install',
            ' '.join(packages)
        ]
        pass_through_environ(argv)
        cp = run_subprocess(argv, universal_newlines=True)
        return cp.returncode

    if not enable_i386():
        return 1

    update_apt()

    # Install the packages using the option "--no-remove" to avoid
    # unexpected dependencies cycle that end up removing packages that are
    # essential for the OS to run
    logger.debug('Installing packages: %s...', ' '.join(packages))
    cp = run_subprocess(
        ['apt-get', 'install', '--no-remove'] + packages,
        universal_newlines=True,
    )

    return cp.returncode


###
def check_config(path, config):
    if "STEAM_RUNTIME" not in config:
        sys.stderr.write(
            "Missing STEAM_RUNTIME definition in %s\n" % path)
        return False

    if config["STEAM_RUNTIME"] not in SUPPORTED_STEAM_RUNTIME:
        sys.stderr.write(
            "Unsupported Steam runtime: %s\n" % config["STEAM_RUNTIME"])
        return False

    if "STEAM_DEPENDENCY_VERSION" not in config:
        sys.stderr.write(
            "Missing STEAM_DEPENDENCY_VERSION definition in %s\n" % path)
        return False

    if config["STEAM_DEPENDENCY_VERSION"]\
            not in SUPPORTED_STEAM_DEPENDENCY_VERSION:
        sys.stderr.write("Unsupported dependency version: %s\n" % config[
            "STEAM_DEPENDENCY_VERSION"])
        return False

    # Make sure we can use dpkg on this system.
    try:
        subprocess.call(['dpkg', '--version'], stdout=subprocess.PIPE)
    except FileNotFoundError:
        sys.stderr.write("Couldn't find dpkg, please update steamdeps for "
                         "your distribution.\n")
        return False

    return True


def update_installed_packages(packages):
    # Get the installed package versions
    # Make sure COLUMNS isn't set, or dpkg will truncate its output
    if "COLUMNS" in os.environ:
        del os.environ["COLUMNS"]

    process = subprocess.Popen(['dpkg', '-l'] + list(packages.keys()),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # The regex first group is the package name, the second group is the
    # version and the third is the architecture
    installed_pattern = re.compile(r"^\Si\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)")
    for line in process.stdout:
        line = line.decode("utf-8").strip()
        match = re.match(installed_pattern, line)
        if match is None:
            continue

        name = match.group(1)
        if name not in packages:
            name = name + ":" + match.group(3)
        packages[name].set_installed(match.group(2))


###
def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    config = {}
    os_release = OsRelease()
    missing_packages = []    # type: typing.List[str]

    parser = argparse.ArgumentParser(description='Install Steam dependencies')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't install anything, just report",
    )
    parser.add_argument(
        '--debug-dump-os-release',
        action='store_true',
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help="This is executed in a terminal that allows user interaction",
    )
    parser.add_argument(
        '--install',
        help="Whitespace separated list of packages to install",
    )
    parser.add_argument(
        '--no-install-confirmation',
        dest='install_confirmation',
        action='store_false',
        help="Do not ask the user for a confirmation before attempting to "
        "install the dependencies",
    )
    parser.add_argument(
        '--setenv',
        action='append',
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--update-apt',
        action='store_true',
        help=(
            "Run apt-get update before evaluating the dependencies to install"
        ),
    )
    parser.add_argument(
        'dependencies',
        metavar='$HOME/.steam/root/steamdeps.txt',
        nargs='?',
        help='Path to steamdeps.txt',
    )
    parser.set_defaults(install_confirmation=True)
    args = parser.parse_args()

    if args.setenv:
        for pair in args.setenv:
            if '=' not in pair:
                logger.error('Expected syntax: --setenv=VAR=VALUE')
                return 2

            var, val = pair.split('=', 1)
            os.environ[var] = val

    if args.install and args.dependencies:
        parser.print_usage(sys.stderr)
        sys.stderr.write(
            "The steamdeps.txt path and --install cannot both be used\n"
        )
        return 2
    elif not args.install and not args.dependencies:
        parser.print_usage(sys.stderr)
        sys.stderr.write(
            "One between the steamdeps.txt path and --install is required\n"
        )
        return 2

    if 'STEAM_LAUNCHER_VERBOSE' in os.environ:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.debug('Run as: %s', ' '.join([quote(a) for a in sys.argv]))

    if args.debug_dump_os_release:
        os_release.dump()
        return 0

    if args.install:
        if args.dry_run:
            logger.debug('Not actually installing %r', args.install)
            return 0

        if not args.interactive:
            argv = get_terminal_wait('Package Install') + [
                os.path.abspath(__file__),
                '--interactive',
            ]
            pass_through_environ(argv)

            if not args.install_confirmation:
                argv.append('--no-install-confirmation')

            argv.extend(['--install', args.install])

            logger.debug(
                'Re-running steamdeps in a terminal to install %r...',
                args.install,
            )
            cp = run_subprocess(
                argv,
                universal_newlines=True,
            )
            return cp.returncode

        packages = sorted(filter(None, args.install.split(' ')))
        return update_packages(packages, args.install_confirmation)

    if args.dry_run:
        logger.debug('Dry-run mode, avoiding side-effects')
    elif args.update_apt or is_apt_out_of_sync() or needs_i386():
        if not args.interactive:
            logger.debug(
                'Re-running steamdeps in an interactive terminal to '
                'be able to update apt cache...',
            )
            argv = get_terminal_wait('Evaluating dependencies') + [
                os.path.abspath(__file__),
                '--interactive',
                '--update-apt',
            ]
            pass_through_environ(argv)
            argv.append(os.path.abspath(args.dependencies))
            cp = run_subprocess(argv, universal_newlines=True)
            return cp.returncode
        elif not is_root():
            # We don't have root privileges, call again this script with pkexec
            print('The packages cache seems to be out of date')
            input('\nPress return to update the list of available packages: ')

            logger.debug(
                'Re-running steamdeps as root to be able to update apt '
                'cache...',
            )
            argv = [
                'pkexec',
                os.path.abspath(__file__),
                '--interactive',
                '--update-apt',
            ]
            pass_through_environ(argv)
            argv.append(os.path.abspath(args.dependencies))
            cp = run_subprocess(argv, universal_newlines=True)

            return cp.returncode

        if not enable_i386():
            return 1

        update_apt()

    # Make sure we can open the file
    try:
        fp = open(args.dependencies)
    except Exception as e:
        sys.stderr.write("Couldn't open file: %s\n" % e)
        return 2

    # Look for configuration variables
    config_pattern = re.compile(r"(\w+)\s*=\s*(\w+)")
    for line in fp:
        line = line.strip()
        if line == "" or line[0] == '#':
            continue

        match = re.match(config_pattern, line)
        if match is not None:
            config[match.group(1)] = match.group(2)

    # Check to make sure we have a valid config
    if not check_config(args.dependencies, config):
        return 3

    # Seek back to the beginning of the file
    fp.seek(0)

    # Load the package dependency information
    packages = {}
    dependencies = []
    for line in fp:
        line = line.strip()
        if line == "" or line[0] == '#':
            continue

        match = re.match(config_pattern, line)
        if match is not None:
            continue

        row = []
        for section in line.split("|"):
            package = create_package(section)
            if package is None:
                continue

            packages[package.name] = package
            row.append(package)

        dependencies.append(row)

    ensure_installed_packages = set()       # type: typing.Set[str]
    archs = [get_arch()]

    if archs[0] == 'amd64' and 'i386' in get_foreign_architectures():
        archs.append('i386')

    for arch in archs:
        for synthetic in (
                'libc6',
                'libegl1',
                'libgbm1',
                'libgl1-mesa-dri',
                'libgl1-mesa-glx',
        ):
            package = create_package(synthetic + ':' + arch)

            if package is not None:
                if package.name not in packages:
                    packages[package.name] = package
                    dependencies.append([package])

                ensure_installed_packages.add(package.name)

    # Try to install these packages, even if they are not
    # listed in the steamdeps.txt file. If they are not available we
    # just inform the user about it and continue.
    for additional_pkg in (
        'steam-libs-amd64:amd64',
        'steam-libs-i386:i386',
        'xdg-desktop-portal',
        choose_xdg_portal_backend() or 'xdg-desktop-portal-gtk',
    ):
        if additional_pkg not in packages:
            if is_package_available(additional_pkg):
                package = Package(additional_pkg, [])
                packages[package.name] = package
                dependencies.append([package])
            else:
                missing_packages.append(additional_pkg)

    # The Steam container runtime (pressure-vessel) requires a setuid
    # bubblewrap executable on some kernel configurations. Steam is
    # unprivileged, so we have to get it from the host OS.
    if (
        # Debian's kernel doesn't allow unprivileged users to create
        # new namespaces (https://bugs.debian.org/898446) so we need the
        # setuid bubblewrap
        os_release.is_os('debian')
        # Ubuntu's kernel does allow that. We assume Ubuntu derivatives
        # like Linux Mint will inherit that, rather than reverting to the
        # Debian behaviour
        and not os_release.is_os('ubuntu')
    ):
        package = Package('bubblewrap', [])
        packages[package.name] = package
        dependencies.append([package])

    nvidia_packages = expected_nvidia_packages()
    for pkg_name in nvidia_packages:
        if pkg_name not in packages:
            if is_package_available(pkg_name):
                packages[pkg_name] = nvidia_packages[pkg_name]
                dependencies.append([nvidia_packages[pkg_name]])
            else:
                missing_packages.append(pkg_name)

    if missing_packages:
        print("These packages are not available:\n")

        for p in sorted(missing_packages):
            print("- %s" % p)

        print("\nThe Steam client may have limited functionality.")

    # Print package dependency information for debug
    if logger.isEnabledFor(logging.DEBUG):
        for row in dependencies:
            if len(row) == 0:
                continue

            logger.debug(
                'Dependency to be checked: %s',
                " | ".join([str(package) for package in row]),
            )

    update_installed_packages(packages)

    # See which ones need to be installed
    needed = set()
    for row in dependencies:
        if len(row) == 0:
            continue

        satisfied = False
        for dep in row:
            if dep.is_available():
                satisfied = True
                break
        if not satisfied:
            needed.add(row[0])

    # If we have anything to install, do it!
    if len(needed) > 0:
        for package in sorted(needed, key=lambda x: x.name):
            if package.installed:
                print("Package %s is installed with version '%s' but doesn't "
                      "match requirements: %s" % (
                        package.name, package.installed, package),
                      file=sys.stderr)
            else:
                print("Package %s needs to be installed" % package.name,
                      file=sys.stderr)

        # If we are going to install additional packages, we also add the
        # ones listed in "ensure_installed_packages". If they were already
        # installed, this forces apt to keep them into consideration when
        # it evaluates the new packages dependencies.
        to_install = set([package.name for package in needed])
        to_install.update(ensure_installed_packages)

        if args.dry_run:
            print(
                'Would run: apt-get install --no-remove {}'.format(
                    ' '.join(sorted(to_install))
                )
            )
            return 1
        else:
            if args.interactive:
                pkgs_names = sorted(to_install)
                return update_packages(pkgs_names, args.install_confirmation)

            logger.debug(
                'Re-running steamdeps in a terminal to install selected '
                'packages',
            )
            argv = get_terminal_wait('Package Install') + [
                os.path.abspath(__file__),
                '--interactive',
            ]
            pass_through_environ(argv)

            if not args.install_confirmation:
                argv.append('--no-install-confirmation')

            argv.extend([
                '--install',
                ' '.join(sorted(to_install)),
            ])

            cp = run_subprocess(
                argv,
                universal_newlines=True,
            )
            return cp.returncode
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
