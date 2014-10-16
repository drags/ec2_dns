$ORIGIN .
$TTL 3600   ; 1 hour
ec2.example.com     IN SOA  ns3.example.com. hostmaster.example.com. (
                2014100911 ; serial
                21600      ; refresh (6 hours)
                3600       ; retry (1 hour)
                604800     ; expire (1 week)
                3600       ; minimum (1 hour)
                )
            NS  ns1.example.com.

$ORIGIN ec2.example.com.
ns1         A   198.199.116.39
$INCLUDE /var/lib/bind/zones/instance_cnames.ec2.example.com.zone
