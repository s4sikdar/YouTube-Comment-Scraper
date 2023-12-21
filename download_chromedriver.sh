#!/usr/bin/env bash

source ./correct_python.sh

# Function to get the operating system. Credit to the following link,
# as I got the function from here: https://gist.github.com/prabirshrestha/3080525
function get_os() {
	os_name=$(uname -o | tr '[:upper:]' '[:lower:]')
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


# The function to get the latest stable version of chrome driver based on the following link below:
# https://googlechromelabs.github.io/chrome-for-testing/ . First we try to use the python script to
# try and download the binary file. If it fails, we try the ducktape hack in this function to hardcode the
# url and make a curl request from there.
function get_latest_chromedriver() {
	platform=''
	os_name=$(get_os)
	#  unzip -l chromedriver_win32.zip | tail -n 4 | head -n 2 | awk '{print $4}'
	machine_hardware_name=$(uname -m | tr '[:upper:]' '[:lower:]')
	tempfile=$(mktemp)
	declare -a bit32
	bit32[0]='i686'
	bit32[1]='i386'
	case ${os_name} in
		linux*)
			if [ "${machine_hardware_name}" = 'x86_64' ]
			then
				platform='linux64'
			else
				echo "You are using linux on a machine that is not 64-bit. You must have a 64-bit machine to have a linux chromedriver. Exiting with an error code of 2." &>2
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
				echo "You are using a Mac OS on a machine that is not an arm-64 machine or a 64-bit machine." &>2
				echo "You must have one of the two to use the linux chromedriver on a Mac OS. Exiting with an error code or 2." &>2
				exit 2
			fi
			;;
		windows*)
			# If machine hardware name is one of the entries in the bit32 array, this is true
			if  [ "${machine_hardware_name}" = "${bit32[0]}" -o "${machine_hardware_name}" = "${bit32[1]}" ]
			then
				platform='win32'
			elif [ "${machine_hardware_name}" = 'x86_64' ]
			then
				platform='win64'
			else
				echo "You are using Windows on an unknown machine that does not support chromedriver. Exiting with an error code of 2" &>2
				exit 2
			fi
			;;
		*)
			echo "Unknown operating system being used that does not support chromedriver. Exiting with an error code of 2." &>2
			exit 2
			;;
	esac
	zip_fname=$(use_correct_python_version ./get_webdriver.py --platform="${platform}" 2> /dev/null)
	if [ -n ${zip_fname} ]
	then
		# unzip -ql ${zip_fname}
		unzip_line_count=$(unzip -ql ${zip_fname} | wc -l)
		line_count_outside_last_2=$((${unzip_line_count} - 2))
		file_count=$((${line_count_outside_last_2} - 2))
		# get all files in the zip file that are not the chromedriver binary and leave them in the zip file
		unzip -ql ${zip_fname} | head -n ${line_count_outside_last_2} | tail -n ${file_count} | awk '/\/chromedriver(.exe)?$/ {print $NF}' > ${tempfile}
		# This only unzips the chromedriver binary
		cat ${tempfile} | xargs unzip ${resulting_fname} -x
	else
		echo "Was unable to download the latest chromedriver binary for some reason. Exiting with an error code of 1." &>2
		exit 1
	fi
}


# The function that ensures the latest stable chromedriver is in your $PATH environment variable.
# Since ~/bin/ is often in the git $PATH environment variable, the function checks if a bin directory
# exists and if it has a chromedriver binary executable with a version equal to the latest stable release.
# If all of this is true, then don't do anything. Otherwise if the bin directory exists but the chromedriver
# binary is not the latest stable release, remove the existing chromedriver binary and download the latest
# stable release. If the bin directory is not there itself, then create a bin directory in your home directory
# and download chrome driver there.
function find_and_install_chromedriver() {
	latest_stable_version=$(curl 'https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE' 2> /dev/null)
	download_endpoint_base='https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/'
	linux_64_zip_path='linux64/chromedriver-linux64.zip'
	mac_arm64_zip_path='mac-arm64/chromedriver-mac-arm64.zip'
	mac_x54_zip_path='mac-x64/chromedriver-mac-x64.zip'
	win32_zip_path='win32/chromedriver-win32.zip'
	win64_zip_path='win64/chromedriver-win64.zip'


	base_dir=$(pwd)
	cd
	home_dir=$(pwd)
	cd - &> /dev/null
	cd ${home_dir}



	if [ -d "bin" ]
	then
		cd bin/
		if [ -s "chromedriver.exe" ]
		then
			local_chrome_version=$(./chromedriver.exe --version 2> /dev/null | awk '{ print $2 }' 2> /dev/null)
			if [ "${local_chrome_version}" != "${latest_stable_version}" ]
			then
				echo "Local chromedriver version is not the latest stable version. Removing the old version and downloading the latest version."
				get_latest_chromedriver
			fi
		else
			echo "bin/ directory exists in ${home_dir} but there is no \"chromedriver.exe\" binary executable. Installing it now"
			get_latest_chromedriver
		fi
	else
		echo "bin directory is not there. Making a bin directory in ${home_dir}"
		mkdir bin
		get_latest_chromedriver
	fi
}


find_and_install_chromedriver
