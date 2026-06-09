#!/usr/bin/env bash
# Install BirdNET script
set -x # Debugging
exec > >(tee -i installation-$(date +%F).txt) 2>&1 # Make log
set -e # exit installation if anything fails

my_dir=$HOME/BirdNET-Pi
export my_dir=$my_dir

cd $my_dir/scripts || exit 1
git log -n 1 --pretty=oneline --no-color --decorate

source install_helpers.sh

if [ "$(uname -m)" != "aarch64" ] && [ "$(uname -m)" != "x86_64" ];then
  echo "BirdNET-Pi requires a 64-bit OS.
It looks like your operating system is using $(uname -m),
but would need to be aarch64."
  exit 1
fi

#Install/Configure /etc/birdnet/birdnet.conf
./install_config.sh || exit 1
sudo -E HOME=$HOME USER=$USER ./install_services.sh || exit 1

if [ -x "$my_dir/scripts/setup_hardware.sh" ] && command -v raspi-config >/dev/null 2>&1; then
  sudo -E HOME=$HOME USER=$USER "$my_dir/scripts/setup_hardware.sh" || exit 1
else
  echo "Skipping hardware setup (setup_hardware.sh or raspi-config not available)."
fi

source /etc/birdnet/birdnet.conf

ensure_lgpio_system_lib() {
  if ldconfig -p 2>/dev/null | grep -q 'liblgpio\.so'; then
    return 0
  fi

  if [ -f /usr/lib/aarch64-linux-gnu/liblgpio.so ] || [ -f /usr/lib/x86_64-linux-gnu/liblgpio.so ]; then
    return 0
  fi

  echo "Installing missing system library for python lgpio package"
  sudo apt-get update -qq

  for pkg in lgpio liblgpio-dev python3-lgpio; do
    if apt-cache show "$pkg" >/dev/null 2>&1; then
      if sudo apt-get install -y "$pkg"; then
        break
      fi
    fi
  done

  if ! ldconfig -p 2>/dev/null | grep -q 'liblgpio\.so'; then
    echo "Could not install liblgpio.so from apt repositories."
    echo "Please install a package that provides liblgpio.so (for example liblgpio-dev) and re-run installer."
    exit 1
  fi
}

install_birdnet() {
  TMP_SIZE=$(df --output=avail /tmp | tail -n 1)
  if [[ $TMP_SIZE -lt 300000 ]]; then
    mkdir -p $HOME/bird_tmp
    export TMPDIR=$HOME/bird_tmp
  fi
  cd ~/BirdNET-Pi || exit 1

  if [ ! -d "$HOME/BirdNET-Pi/e-Paper/.git" ]; then
    if [ ! -d "$HOME/BirdNET-Pi/e-Paper" ]; then
      git clone https://github.com/waveshare/e-Paper.git "$HOME/BirdNET-Pi/e-Paper"
    else
      echo "Found existing $HOME/BirdNET-Pi/e-Paper directory without git metadata, skipping clone."
    fi
  else
    git -C "$HOME/BirdNET-Pi/e-Paper" pull --ff-only || true
  fi

  # Add sslip domain to cloud-init template if not already present
  echo "192.168.4.1    192-168-4-1.sslip.io" | sudo tee -a /etc/cloud/templates/hosts.debian.tmpl

  echo "Establishing a python virtual environment"
  python3 -m venv birdnet
  source ./birdnet/bin/activate
  pip3 install wheel
  get_tf_whl
  ensure_lgpio_system_lib
  LOOP_COUNT=2
  while ! pip3 install -U -r ./requirements_custom.txt
  do
    LOOP_COUNT=$(( LOOP_COUNT - 1 ))
    pip3 cache purge
    [ $LOOP_COUNT == 0 ] && exit 1
    sleep 5
  done
  pip3 install pillow gpiozero lgpio spidev
  rm -rf $HOME/bird_tmp
}

[ -d ${RECS_DIR} ] || mkdir -p ${RECS_DIR} &> /dev/null

install_birdnet

cd $my_dir/scripts || exit 1

# tzlocal.get_localzone() will fail if the Debian specific /etc/timezone is not in sync
CURRENT_TIMEZONE=$(timedatectl show --value --property=Timezone)
[ -f /etc/timezone ] && echo "$CURRENT_TIMEZONE" | sudo tee /etc/timezone > /dev/null

./install_language_label.sh || exit 1

exit 0
