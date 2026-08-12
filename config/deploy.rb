# frozen_string_literal: true

set :application, 'pricing-calc'
set :repo_url, 'git@github.com:reabd/Pricing-Calc.git'
set :deploy_to, '~/pricing-calc'
set :deploy_user, 'deploy'
set :format, :pretty
set :log_level, :info
set :pty, true
set :use_sudo, false
set :keep_releases, 5

set :linked_files, []
set :linked_dirs, %w[venv]

set :pricing_calc_service, 'okapics-pricing-calc'
set :pricing_calc_port, '5050'

# net-ssh 6.1 cipher restrictions (same as okapics config/deploy.rb).
# Capfile sets forward_agent last, matching okapics deploy behaviour.
set :ssh_options, {
  encryption: %w[aes256-ctr aes192-ctr aes128-ctr],
  hmac: %w[hmac-sha2-512-etm@openssh.com hmac-sha2-256-etm@openssh.com hmac-sha2-512 hmac-sha2-256 hmac-sha1]
}

namespace :deploy do
  desc 'Install Python dependencies into shared venv'
  task :pip_install do
    on roles(:app) do
      venv_path = shared_path.join('venv')
      venv_python = venv_path.join('bin/python')
      pip = venv_path.join('bin/pip')

      unless test("[ -x #{pip} ]")
        execute :rm, '-rf', venv_path
        execute :python3, '-m', 'venv', venv_path
        execute venv_python, '-m', 'ensurepip', '--upgrade'
      end

      within release_path do
        execute venv_python, '-m', 'pip', 'install', '-r', 'requirements.txt'
      end
    end
  end

  after :updated, 'deploy:pip_install'
  after :published, 'pricing_calc:restart'
end
