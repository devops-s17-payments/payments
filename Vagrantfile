# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.

unless Vagrant.has_plugin?("vagrant-docker-compose")
  system("vagrant plugin install vagrant-docker-compose")
  puts "Dependencies installed, please try the command again."
  exit
end

Vagrant.configure(2) do |config|
  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "ubuntu/trusty64"

  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 5000, host: 5000 #flask
  #config.vm.network "forwarded_port", guest: 5432, host: 5432 #postgres

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  config.vm.network "private_network", ip: "192.168.33.10"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider "virtualbox" do |vb|
    # Customize the amount of memory on the VM:
    vb.memory = "512"
    vb.cpus = 1
  end

  # Copy your .gitconfig file so that your git credentials are correct
  if File.exists?(File.expand_path("~/.gitconfig"))
    config.vm.provision "file", source: "~/.gitconfig", destination: "~/.gitconfig"
  end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
    sudo apt-get update
    sudo apt-get install -y git zip tree python-pip python-dev build-essential libpq-dev
    sudo apt-get -y autoremove

    # Install the Cloud Foundry CLI
    wget -O cf-cli-installer_6.24.0_x86-64.deb 'https://cli.run.pivotal.io/stable?release=debian64&source=github'
    sudo dpkg -i cf-cli-installer_6.24.0_x86-64.deb
    rm cf-cli-installer_6.24.0_x86-64.deb
    
    # Install app dependencies
    cd /vagrant
    sudo pip install -r requirements.txt
    
    # Make vi look nice
    echo "colorscheme desert" > ~/.vimrc
  SHELL


  ######################################################################
  # Add PostgreSQL docker container
  ######################################################################
  # Prepare PostgreSQL provisioning - make needed directories and export env variables
  config.vm.provision "shell", path: "db_provision.sh", 
    env: {"DB_NAME" => ENV["DB_NAME"], "DB_USER" => ENV["DB_USER"], "DB_PASSWORD" => ENV["DB_PASSWORD"]}

  # Add the dev PostgreSQL docker container
  # Note: the "d" essentially refers to the "docker" CLI command
  # hence, d.pull_images -> "docker pull <image_name>"
  config.vm.provision "docker" do |d|
    d.pull_images "postgres"
    #d.run "postgres",
      #args: "-d --name payments-database -p 5432:5432 -v /var/lib/postgresql/data -e POSTGRES_USER=payments -e POSTGRES_PASSWORD=payments -e POSTGRES_DB=dev"
  end

  # add docker_compose file
  config.vm.provision :docker_compose

end
