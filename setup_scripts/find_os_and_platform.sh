#!/usr/bin/env bash

# Function to get the operating system. Credit to the following link,
# as I got the function from here: https://gist.github.com/prabirshrestha/3080525
function get_os() {
	os_name=$(uname | tr '[:upper:]' '[:lower:]')
	case ${os_name} in
		linux*)
			echo "linux"
			;;
		darwin*)
			echo "darwin"
			;;
		msys*|cygwin*|mingw*)
			echo "windows"
			;;
		nt|win*)
			echo "windows"
			;;
		*)
			echo "unknown"
			;;
	esac
}


# The function that helps us to get the name of the platform being used. Using the machine hardware names and the operating
# system specified, we can determine the platform that we are on. This determines what chromedriver zip file we must download.
# If we see a operating system and hardware combination that is not supported, we immediately alert the user by printing to standard error and exiting with an error code of 2.
function get_platform() {
	platform=''
	os_name=$(get_os)
	# run uname -m to get the machine of the platform, and use the tr command to guarantee everything is lowercase
	machine_hardware_name=$(uname -m | tr '[:upper:]' '[:lower:]')
	tempfile=$(mktemp)
	declare -a windows_bit32_hardware_names
	windows_bit32_hardware_names[0]='i686'
	windows_bit32_hardware_names[1]='i386'
	case ${os_name} in
		linux*)
			if [ "${machine_hardware_name}" = 'x86_64' ]
			then
				platform='linux64'
			else
				echo "You are using linux on a machine that is not 64-bit. On Linux, you must have a 64-bit machine to use chromedriver. Exiting with an error code of 2." 1>&2
				rm ${tempfile}
				exit 2
			fi
			;;
		darwin*)
			if  [ "${machine_hardware_name}" = 'arm64' ]
			then
				platform='mac-arm64'
			elif [ "${machine_hardware_name}" = 'x86_64' ]
			then
				platform='mac-x64'
			else
				echo "You are using a Mac OS on a machine that is not an mac-arm64 machine or a mac-x64 machine." 1>&2
				echo "You must have one of the two to use chromedriver on a Mac OS. Exiting with an error code or 2." 1>&2
				rm ${tempfile}
				exit 2
			fi
			;;
		windows*)
			# If machine hardware name is one of the entries in the windows_bit32_hardware_names array, this condition is true
			if  [ "${machine_hardware_name}" = "${windows_bit32_hardware_names[0]}" -o "${machine_hardware_name}" = "${windows_bit32_hardware_names[1]}" ]
			then
				platform='win32'
			elif [ "${machine_hardware_name}" = 'x86_64' ]
			then
				platform='win64'
			else
				echo "You are using Windows on an unknown machine that does not support chromedriver. Exiting with an error code of 2" 1>&2
				rm ${tempfile}
				exit 2
			fi
			;;
		*)
			echo "Unknown operating system being used that does not support chromedriver. Exiting with an error code of 2." 1>&2
			rm ${tempfile}
			exit 2
			;;
	esac
	echo ${platform} # output from this function is used as an argument for the get_webdriver.py script.
	rm ${tempfile}
}
