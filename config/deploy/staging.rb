# frozen_string_literal: true

set :stage, :staging
set :branch, 'staging'

append :linked_files, '.env.staging'

server '139.162.136.184', user: 'deploy', roles: %w[app web]
