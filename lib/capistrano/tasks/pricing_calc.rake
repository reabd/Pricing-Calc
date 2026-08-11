# frozen_string_literal: true

namespace :pricing_calc do
  desc 'Restart Pricing-Calc systemd service'
  task :restart do
    on roles(:app), in: :sequence, wait: 5 do
      service_name = fetch(:pricing_calc_service, 'okapics-pricing-calc')
      execute :sudo, :systemctl, :restart, service_name
    end
  end
end
