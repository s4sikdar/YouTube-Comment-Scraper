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
function get_platform() {
	platform=''
	os_name=$(get_os)
	# run uname -m to get the machine of the platform, and use the tr command to guarantee everything is lowercase
	machine_hardware_name=$(uname -m | tr '[:upper:]' '[:lower:]')
	tempfile=$(mktemp)
	# machine hardware names for bit32 hardware
	declare -a bit32_hardware_names
	bit32_hardware_names[0]='i686'
	bit32_hardware_names[1]='i386'
	case ${os_name} in
		linux*)
			if [ "${machine_hardware_name}" = 'x86_64' ]
			then
				platform='linux64'
			else
				echo "You are using linux on a machine that is not 64-bit. You must have a 64-bit machine to have a linux chromedriver. Exiting with an error code of 2." 1>&2
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
				echo "You are using a Mac OS on a machine that is not an arm-64 machine or a 64-bit machine." 1>&2
				echo "You must have one of the two to use the linux chromedriver on a Mac OS. Exiting with an error code or 2." 1>&2
				rm ${tempfile}
				exit 2
			fi
			;;
		windows*)
			# If machine hardware name is one of the entries in the bit32_hardware_names array, this is true
			if  [ "${machine_hardware_name}" = "${bit32_hardware_names[0]}" -o "${machine_hardware_name}" = "${bit32_hardware_names[1]}" ]
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
	echo ${platform}
	rm ${tempfile}
}



# The function uses the python script to download the latest chromedriver binary available for google chrome. From there it
# extracts the chromedriver binary only from the zip file using the unzip command (if possible). It then prints the output of
# the file path that has been extracted from the unzip command. One argument is given, which is the name of the python script path.
function get_latest_chromedriver() {
	python_script_path="${1}"
	tempfile=$(mktemp)
	#error_output_file=$(mktemp)
	# Since standard error is redirected to /dev/null, a non-zero exit code from the get_platform function will result in
	# platform being an empty string. Enter the if conditional if the string has a length of 0.
	platform=$(get_platform 2> /dev/null)
	if [ -z "${platform}" ]
	then
		# Since it's a subshell, the return code should exit out of the subshell. So run the command again.
		# This time, don't show standard output. Show standard error only. Since it is not in a subshell this time,
		# the script should exit.
		rm ${tempfile}
		get_platform 1> /dev/null
	fi
	# Since standard error is redirected to /dev/null, a non-zero exit code from the command in the subshell will result in
	# platform being an empty string. Enter the if conditional if the string in zip_fname has a non-zero length.
	zip_fname=$(use_correct_python_version "${python_script_path}" --platform="${platform}" 2> /dev/null)
	if [ "${zip_fname}" ]
	then
		# Test that we have the unzip command installed
		unzip -v &> /dev/null
		if [ ${?} -ne 0 ]
		then
			#set +x
			echo "The file ${zip_fname} was downloaded but the unzip command does not seem to be supported." 1>&2
			echo "You will need to manually unzip the chromedriver zip file, take out the chromedriver binary, and install it in your PATH." 1>&2
			echo "Exiting with an error code of 1." 1>&2
			rm ${tempfile}
			exit 1
		fi
		# unzil -ql ${zip_filename} shows the file structure of what is inside of the zip file, with other information as well.
		# The first 2 and last 2 lines are for decoration. So the actual line count is the line count from unzip -ql "file name" - 4
		unzip_line_count=$(unzip -ql "${zip_fname}" 2> /dev/null | wc -l 2> /dev/null)
		line_count_outside_last_2=$((${unzip_line_count} - 2))
		actual_file_count=$((${line_count_outside_last_2} - 2))
		# get all files in the zip file that are not the chromedriver binary and print them to a tempfile.
		unzip -ql ${zip_fname} 2> /dev/null | head -n ${line_count_outside_last_2} 2> /dev/null | tail -n ${actual_file_count} 2> /dev/null | awk '!/\/chromedriver(.exe)?$/ {print $NF}' > ${tempfile} 2> /dev/null
		tempfile_char_count=$(wc -c ${tempfile} | awk '{ print $1 }' 2> /dev/null)
		if [[ ${tempfile_char_count} -eq 0 ]]
		then
			echo "Something when wrong when trying to unzip. You iwll have to manually unzip the chromedriver zip file, take out the chromedriver binary and add it to your PATH." 1>&2
			echo "Exiting with an error code of 1." 1>&2
			echo "" > ${tempfile}
			rm ${tempfile}
			exit 1
		else
			# Use the tempfile contents as input for files unzip should ignore when unzipping files (specified with the -x flag in the unzip command)
			unzip -ql ${zip_fname} 2> /dev/null | head -n ${line_count_outside_last_2} 2> /dev/null | tail -n ${actual_file_count} 2> /dev/null | awk '/\/chromedriver(.exe)?$/ {print $NF}'
			cat ${tempfile} | xargs unzip -q "${zip_fname}" -x
		fi
		echo "" > ${tempfile}
		rm ${tempfile}
	else
		echo "Was unable to download the latest chromedriver binary for some reason. Exiting with an error code of 1." 1>&2
		rm ${tempfile}
		exit 1
	fi
}

# find_and_install_chromedriver gets the chromedriver executable, and puts it into ~/bin/. Everything else is removed.
# Three arguments are taken:
# 1) ${1} contains the absolute path to the python script
# 2) ${2} contains the executable name
# 3) ${3} contains the name of the zip file
# Requires: the script must be in ~/bin/ when this is called
function download_and_move_chromedriver_locally() {
	# get_latest_chromedriver prints out the path to the chromedriver executable from ~/bin/.
	# If the path is different (i.e. chromedriver is in another nested directory, copy the executable into ~/bin/ and remove the original different path).
	# Otherwise, do nothing to the path to the chromedriver executable. Also we remove the zip file.
	python_script_path="${1}"
	executable_name="${2}"
	zip_file_name="${3}"
	chromedriver_executable_path=$(get_latest_chromedriver "${python_script_path}" 2> /dev/null)
	#chromedrivers_in_bin_dir=$(find -maxdepth 1 -type f -iname "${executable_name}" 2> /dev/null)
	num_fields_seprated_by_slash=$(echo "${chromedriver_executable_path}" | awk -F / '{ print NF }')
	directory_name=$(echo "${chromedriver_executable_path}" | awk -F / '{ print $1 }')
	# Essentially we don't know the file structure inside the zip file until we use the unzip command.
	# The chromedriver executable could be in multiple subdirectories that get created. So if the number of fields
	# separated by a slash is greater than 1, then we know that we need to copy the original path to the chromedriver
	# executable and put it in the main ~/bin/ directory. Then we remove the directory name for the chromedriver executable
	# path (if applicable), and the zipfile.
	if [[ ${num_fields_seprated_by_slash} -gt 1 ]]
	then
		#cat ${error_output_file}
		# In the special case that we have the executable name being the same as the directory name, we create a placeholder
		# directory, copy the executable there, remove the directory with the same name as the executable, then copy the executable
		# out of the placeholder directory and into ~/bin/. Then we remove the placeholder directory.
		if [ "${directory_name}" = "${executable_name}" ]
		then
			echo "Chromedriver executable is in ~/bin/${chromedriver_executable_path}. Moving executable to ~/bin/ and removing both directory ${directory_name}/ and ${zip_file_name}."
			num=1
			placeholder_dir="testdir${num}"
			while [ -d "${placeholder_dir}" ]
			do
				num=$($(${num} + 1))
				placeholder_dir="testdir${num}"
			done
			mkdir "${placeholder_dir}"
			cp "./${chromedriver_executable_path}" "./${placeholder_dir}/"
			rm -r "./${directory_name}/"
			cp "./${placeholder_dir}/${executable_name}" "./${executable_name}"
			rm -r "./${placeholder_dir}/"
		else
			echo "Chromedriver executable is in ~/bin/${chromedriver_executable_path}. Moving executable to ~/bin/ and removing both directory ${directory_name}/ and ${zip_file_name}."
			cp "${chromedriver_executable_path}" "./${executable_name}"
			rm -r "./${directory_name}/"
		fi
		#rm ${error_output_file}
	fi
	rm "${zip_file_name}"
}

# The function that ensures the following:
# 1) A ~/bin/ directory exists and it is in your $PATH variable. Otherwise create the ~/bin/ directory if necessary, and warn the user if it is not included in their path directory.
# 2) Inside the ~/bin/ directory is the latest stable version of chromedriver based on an endpoint in the function. Otherwise download the latest version.
function find_and_install_chromedriver() {
	latest_stable_version_endpoint='https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE'
	latest_stable_version=$(curl -s "${latest_stable_version_endpoint}" 2> /dev/null)
	linux_64_zip_name='chromedriver-linux64.zip'
	mac_arm64_zip_name='chromedriver-mac-arm64.zip'
	mac_x64_zip_name='chromedriver-mac-x64.zip'
	win32_zip_name='chromedriver-win32.zip'
	win64_zip_name='chromedriver-win64.zip'
	project_path=$(pwd)
	python_script_path="${project_path}/get_webdriver.py"
	cd ${HOME}


	platform_name=$(get_platform)
	executable_name='chromedriver'
	zip_file_name=''
	case ${platform_name} in
		win32*)
			executable_name='chromedriver.exe'
			zip_file_name="${win32_zip_name}"
			;;
		win64*)
			executable_name='chromedriver.exe'
			zip_file_name="${win64_zip_name}"
			;;
		linux64*)
			executable_name='chromedriver'
			zip_file_name="${linux_64_zip_name}"
			;;
		mac-arm64*)
			executable_name='chromedriver'
			zip_file_name="${mac_arm64_zip_name}"
			;;
		mac-x64*)
			executable_name='chromedriver'
			zip_file_name="${mac_x64_zip_name}"
			;;
		*)
			echo "Unknown platform that does not support chromedriver. Exiting with an error code of 2." 1>&2
			exit 2
			;;
	esac
	if [ -d "bin" ]
	then
		cd bin/
		if [ -s "${executable_name}" ]
		then
			local_chromedriver_version=$(./${executable_name} --version 2> /dev/null | awk '{ print $2 }' 2> /dev/null)
			# if local_chromedriver_version is an empty string, or does not equal latest stable version, then remove the local chromedriver executable
			# and download the latest one, because it is either not up to date, or something went wrong.
			if [ -z "${local_chromedriver_version}" -o "${local_chromedriver_version}" != "${latest_stable_version}" ]
			then
				echo "Local chromedriver version is not the latest stable version or the version could not be gathered. In both cases, something is wrong."
				echo "Downloading the latest version of chromedriver and removing the existing file with the same name as the executable name."
				rm "${executable_name}"
				download_and_move_chromedriver_locally "${python_script_path}" "${executable_name}" "${zip_file_name}"
			fi
		else
			echo "${HOME}/bin/ directory exists in ${HOME} but there is no \"chromedriver.exe\" binary executable. Installing it now."
			download_and_move_chromedriver_locally "${python_script_path}" "${executable_name}" "${zip_file_name}"
		fi
	else
		echo "bin directory is not there. Making a bin directory in ${HOME}"
		mkdir bin
		cd bin/
		download_and_move_chromedriver_locally "${python_script_path}" "${executable_name}" "${zip_file_name}"
	fi
	if [[ ":${PATH}:" != *":${HOME}/bin:"* ]]
	then
		echo "${HOME}/bin/ is not in your path directory. The script will add this directory to your path environment variable."
		PATH="${HOME}/bin:${PATH}"
	fi
	echo "Setup is complete."
}


find_and_install_chromedriver
