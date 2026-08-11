# frozen_string_literal: true

require 'capistrano/setup'
require 'capistrano/deploy'
require 'capistrano/scm/git'
install_plugin Capistrano::SCM::Git

Dir.glob('lib/capistrano/tasks/*.rake').each { |r| import r }

# Match okapics Capfile — must come after deploy.rb is loaded so this wins.
set :ssh_options, { forward_agent: true }
