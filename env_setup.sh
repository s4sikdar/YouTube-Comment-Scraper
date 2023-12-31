#!/usr/bin/env bash

source ./setup_scripts/correct_python.sh
source ./setup_scripts/download_chromedriver.sh
project_dir=$(pwd)

# Color constants used for printing messages in color.
YELLOW='\033[0;33m'       # Yellow
NC='\033[0m' 		  # No Color
GREEN='\033[0;32m'        # Green
LIGHT_RED='\033[1;31m'    # Light Red
LIGHT_GREEN='\033[1;32m'  # Light Green \033[1;32m

# Global variables used in the script
virtual_env_name="virtual_env_dependencies"
no_caching=false
color=false
filename="requirements.txt"
continue_setup=true
get_chromedriver=false


# Print the below help message
function usage() {
	# cat << EOF prints out text and stops printing the moment it matches the text found after '<<'
	cat << EOF
Usage:
./env_setup.sh [-e <virtual environment name>] [-n] [-c] [-h] [ -f <text file name containing output of pip freeze> ] [-d]
OR
source env_setup.sh [-e <virtual environment name>] [-n] [-c] [-h] [ -f <text file name containing output of pip freeze> ] [-d]

Description:
This script the setup for the virtual envirnoment to install all dependencies in an isolated environment.
The script first looks for the recommended virtual environment directory (which can be specified as a command line argument),
and if it exists, it compares the dependencies installed with the dependencies in the requirements.txt file. If the dependencies
are not matching, all existing dependencies are uninstalled and the dependencies specified in requirements.txt are installed instead.

**********************************************************VERY IMPORTANT*************************************************************

YOU MUST HAVE A TEXT FILE THAT CONTAINS THE OUTPUT OF "pip freeze" IN YOUR DIRECTORY. IF THIS FILE IS NOT "requirements.txt", IT MUST BE
SPECIFIED WITH THE -f COMMAND LINE OPTION. OTHERWISE THIS SCRIPT WILL HAVE UNDEFINED BEHAVIOURS. THEY MAY CHANGE YOUR LOCAL ENVIRONMENT.
THIS IS A FAIR WARNING.

*************************************************************************************************************************************

*******************************************************Important suggestion**********************************************************

It is recommended to run the second version (source env_setup.sh) to so that the virtual environment is loaded
into your terminal, and you can run the script from there. Otherwise you have to run the command below (for git bash at least).
source ./\${DIRNAME}/Scripts/activate

*************************************************************************************************************************************

Arguments supported:
-h	Display this help message and exit immediately if this is specified.

-e	Specify the virtual environment directory name. By default this is "virtual_env_dependencies".

-n	Does not use cached packages when managing dependencies. This installs packages with the --no-cache-dir
	flag, and purges the cache with "pip cache purge" when uninstalling dependencies. This will upgrade pip
	with the --no-cache-dir flag as well. If you specify this, then the script will take more time and cause
	significantly more network usage.

-c	Print color messages. Print messages in yellow or green (yellow means some adjustment is being made,
	green means the packages have all been installed successfully). This is disabled by default.

-f	Specify the filename that has the listed dependencies you install. This filename should be the output
	of "pip freeze". By default it is "requirements.txt".

-d	When d is specfied, the script checks that ${HOME}/bin/ exists, and that inside the ${HOME}/bin/ directory is the latest version of chromedriver.
	If this is not true, the script will create the ${HOME}/bin/ directory, download the latest version of chromedriver and store it in ${HOME}/bin/.
	If ${HOME}/bin/ is not in your PATH environment variable, the script will then ask permission to add it to your PATH environment variable.
	If you enter 'y', then this will be added to your PATH variable in your current bash session (assuming you run this script with the source command).
	Otherwise, you have to move the executable to a directory that is included in your PATH environment variable.

Examples:
./setup -h 					# Prints this help message
./setup -e dirname				# Specifies the virtual environment directory name to be "dirname"
./setup -n					# disable caching
./setup -c					# print color messages
./setup -c -n -e dependencies			# disable caching, sets the virtual environment directory name to be "dependencies", and enables color messaging
./setup						# sets the virtual environment directory to be the default: "virtual_env_dependencies" (and continues from there)
./setup -f dependencies.txt			# sets the dependency text file to be used to be "dependencies.txt". All else is default.
./setup -e dirname -d				# Specifies the virtual environment directory name to be "dirname", and downloads and stores the latest chromedriver in ${HOME}/bin/.
EOF
}


# Print text in color. One argument is allowed, which is the color code.
# The text you want to change in color should be passed in as input to this function
# (i.e. through redirection - e.g. 'echo "Hello World" | print_color "${GREEN}"')
function print_color() {
	if [ ${#} -eq 1 ]
	then
		echo -en "${1}"
	else
		echo -en "${NC}"
	fi
	if [ "${color}" = false ]
	then
		echo -en "${NC}"
	fi
	cat -
	echo -en "${NC}"
}



# Upgrade pip when an upgrade is available, --no-cache-dir is run to disable caching if that argument is specified
function upgrade_pip() {
	if [ "${1}" = true ]
	then
		use_correct_python_version -m pip install --upgrade pip --quiet --no-cache-dir
	else
		use_correct_python_version -m pip install --upgrade pip --quiet
	fi
}


# Install dependencies with pip install. --no-cache-dir is run to disable caching if that argument is specified
function install_dependencies() {
	if [ "${1}" = true ]
	then
		use_correct_python_version -m pip install -r ${filename} --quiet --no-cache-dir
	else
		use_correct_python_version -m pip install -r ${filename} --quiet
	fi
}


# function to remove the existing directory with the name of the virtual environment, and crate a new one
# in its place. From there, find the location of the "activate" bash script and source it so that you've activated
# the new script. From there, upgrade pip and install all required dependencies.
function remove_and_reinstall_venv() {
	env_name="${1}"
	echo "Existing \"${env_name}\" directory found that is not a virtual environment directory." | print_color "${YELLOW}"
	echo "This script will delete it, install a new virtual environment with directory name \"${env_name}\", and install dependencies." | print_color "${YELLOW}"
	rm -r "./${env_name}"
	use_correct_python_version -m venv "./${env_name}"
	activate_script=$(find  ./ -iwholename "./${env_name}/*/activate" 2> /dev/null)
	source "${activate_script}" 2> /dev/null
	upgrade_pip "${no_caching}"
	install_dependencies "${no_caching}"
	echo "Requirements have been installed." | print_color "${GREEN}"
}


OPTIND=1
# The part of the script that parses arguments passed into the command line. The script uses getopts, which should be compatible across platforms,
if [ ${#} -ne 0 ]
then
	while getopts ":he:f:ncd" arg_value
	do
		case ${arg_value} in
			h)
				usage
				continue_setup=false
				break
				;;
			e)
				virtual_env_name="${OPTARG}"
				;;
			f)
				filename="${OPTARG}"
				if [ ! -f "${filename}" ]
				then
					echo "${filename} does not exist. Using \"requirements.txt\"" | print_color "${YELLOW}"
					filename="requirements.txt"
				fi
				;;
			n)
				no_caching=true
				;;
			c)
				color=true
				;;
			d)
				get_chromedriver=true
				;;
			\?)
				echo "Invalid usage. Run ./env_setup.sh -h for documentation on how to use this script" 1>&2
				continue_setup=false
				;;
		esac
	done
	shift $((${OPTIND}-1))
fi


function run_setup() {
	tempfile=$(mktemp)
	diff_output=$(mktemp)
	if [ -d "${virtual_env_name}" ]
	then
		# Directory was found, so try activating the script to start the virtual environment. If it doesn't work (non-zero return code), then
		# remove this directory and install a new virtual environment with the same directory name. If it works, then check the existing package
		# dependencies.
		activate_script=$(find  ./ -iwholename "./${virtual_env_name}/*/activate" 2> /dev/null)
		if [ ! -z "${activate_script}" ]
		then
			source "${activate_script}" 2> /dev/null
			if [ ${?} -ne 0 ]
			then
				remove_and_reinstall_venv "${virtual_env_name}"
			else
				# Check the current package dependency listing and compare it with requirements.txt using the diff command to determine if there
				# are any differences in package installed (i.e. different version, different packages installed, etc.)
				use_correct_python_version -m pip freeze > ${tempfile}
				# flags on diff command ensure we don't worry about differences in space change
				diff ${tempfile} ./requirements.txt -ZEbB > ${diff_output}
				lines_difference=$(wc -l ${diff_output} | awk '{ print $1 }')
				if [ ${lines_difference} -gt 0 ]
				then
					echo "Existing package installations were found that differ from the dependencies in ${filename}" | print_color "${YELLOW}"
					echo "Removing all existing dependencies and installing the dependencies in ${filename}" | print_color "${YELLOW}"
					upgrade_pip "${no_caching}"
					use_correct_python_version -m pip uninstall -r ${tempfile} -y --quiet
					if [ "${no_caching}" = true ]
					then
						use_correct_python_version -m pip cache purge 2> /dev/null
					fi
					install_dependencies "${no_caching}"
					echo "Requirements have been installed." | print_color "${GREEN}"
				fi
				upgrade_pip "${no_caching}"
			fi
		else
			remove_and_reinstall_venv "${virtual_env_name}"
		fi
		#source ./${virtual_env_name}/Scripts/activate 2> /dev/null
		#if [ ${?} -ne 0 ]
		#then
		#	echo "Existing \"${virtual_env_name}\" directory found that is not a virtual environment directory." | print_color "${YELLOW}"
		#	echo "This script will delete it, install a new virtual environment with directory name \"${virtual_env_name}\", and install dependencies." | print_color "${YELLOW}"
		#	rm -r "./${virtual_env_name}"
		#	use_correct_python_version -m venv "./${virtual_env_name}"
		#	source ./${virtual_env_name}/Scripts/activate
		#	upgrade_pip "${no_caching}"
		#	install_dependencies "${no_caching}"
		#	echo "Requirements have been installed." | print_color "${GREEN}"
		#else
		#	# Check the current package dependency listing and compare it with requirements.txt using the diff command to determine if there
		#	# are any differences in package installed (i.e. different version, different packages installed, etc.)
		#	use_correct_python_version -m pip freeze > ${tempfile}
		#	diff ${tempfile} ./requirements.txt -ZEbB > ${diff_output}
		#	lines_difference=$(wc -l ${diff_output} | awk '{ print $1 }')
		#	if [ ${lines_difference} -gt 0 ]
		#	then
		#		echo "Existing package installations were found that differ from the dependencies in ${filename}" | print_color "${YELLOW}"
		#		echo "Removing all existing dependencies and installing the dependencies in ${filename}" | print_color "${YELLOW}"
		#		upgrade_pip "${no_caching}"
		#		use_correct_python_version -m pip uninstall -r ${tempfile} -y --quiet
		#		if [ "${no_caching}" = true ]
		#		then
		#			use_correct_python_version -m pip cache purge 2> /dev/null
		#		fi
		#		install_dependencies "${no_caching}"
		#		echo "Requirements have been installed." | print_color "${GREEN}"
		#	fi
		#	upgrade_pip "${no_caching}"
		#fi
	else
		# If the length variable is 0, then there is no existing directory with the given virtual environment name. Create a virtual environment
		# with this directory name and install all of the dependencies.
		echo "No existing virtual environment found with directory name \"${virtual_env_name}\"." | print_color "${YELLOW}"
		echo "Creating a new virtual environment with directory name \"${virtual_env_name}\" and installing the dependencies listed in ${filename}" | print_color "${YELLOW}"
		use_correct_python_version -m venv "./${virtual_env_name}"
		#source ./${virtual_env_name}/Scripts/activate
		activate_script=$(find  ./ -iwholename "./${virtual_env_name}/*/activate" 2> /dev/null)
		source "${activate_script}" 2> /dev/null
		upgrade_pip "${no_caching}"
		install_dependencies "${no_caching}"
		echo "Requirements have been installed." | print_color "${GREEN}"
	fi

	# If the command line argument is specified, then find and install chromedriver
	if [ ${get_chromedriver} = 'true' ]
	then
		echo "Checking chromedriver installation in ${HOME}/bin/ now." | print_color "${YELLOW}"
		find_and_install_chromedriver | print_color "${YELLOW}"
		cd "${project_dir}"
	fi
	rm ${tempfile}
	rm ${diff_output}
}

if [ ! -f "${filename}" ]
then
	# continue_setup dictates if we should continue our setup or not. If the text file containing the output of "pip freeze" is not there,
	# then we should not continue unless another text file is present that is specified through the command line. In this case, the getopts
	# command will have a case to accountt for this and switch this variable back to true.
	echo "${filename} does not exist after checking. Add a text file with the output of \"pip freeze\" and specify it in the command line if it is not requirements.txt." | print_color "${LIGHT_RED}"
	echo "Not continuing with the setup." | print_color "${LIGHT_RED}"
	continue_setup=false
fi

if [ "${continue_setup}" = true ]
then
	run_setup
fi
