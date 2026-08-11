# frozen_string_literal: true

set :stage, :production
set :branch, 'main'

server '139.162.161.125', user: 'deploy', roles: %w[app web]
