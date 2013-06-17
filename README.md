Need to define 

- a new nrpe command in nagios

define command {	
  command_name nrpe_slow	
  command_line $USER1$/check_nrpe -H $HOSTADDRESS$ -c $ARG1$ -t $ARG2$	
}

- a service to check with the nrpe_slow 

define service {
  hostgroup_name varnish.hostname.local
  servicegroups varnish
  service_description Check varnish backend fail.
  check_command nrpe_slow!check_varnish_backend_fail!30
  use default_service_template
}

