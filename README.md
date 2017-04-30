# SDN_Loadbalancing

OBJECTIVE: To perform SDN Load balancing on fat tree topology using SDN Controller - Floodlight.


Running the Program (Floodlight)
Note: We are performing load balancing between h1, h3 and h4 at the moment. The best path for both is via Switch 1 Port 4.

1.	Remove the official Floodlight Load Balancer
2.	Run the floodlight.sh shell script
3.	Run Floodlight
$ cd floodlight-1.2
$ ant
$ sudo chmod 777 /var/lib/floodlight
$ java -jar target/floodlight.jar

OPEN TERMINAL FOR MININET
1.	Run the fat tree topology i.e. topology.py using Mininet
$ sudo mn --custom topology.py --topo mytopo --controller=remote,ip=127.0.0.1,port=6653
2.	Type the following command in Mininet
    mininet> xterm h1 h1

OPEN XTERM – 2 H1 NODES
1.	In first console of h1 type, ``` ping 10.0.0.3 ```
2.	In second console of h1 type, ``` ping 10.0.0.4 ```

OPEN WIRESHARK FROM NEW TERMINAL 
1.	On Terminal open a new tab ``` Ctrl + Shift + T ``` and type ``` sudo wireshark ```
2.	In wireshark, go to Capture->Interfaces and select ``` s1-eth4 ``` and start the capture.
3.	In filters section in wireshark type ``` ip.addr==10.0.0.3 ``` and check if you are receiving packets for h1 -> h3. Do same thing for h1->h4. Once you see packets, you can figure that this is the best path.
4.	But to confirm it is, repeat the above two steps for ``` s1-eth3 ``` and you will find that no packets are transmitted to this port. Only packets it will receive will be broadcast and multicast. Ignore them.

CREATE CONGESTION ON BEST PATH OF H1 -> H3
Now in the second console of xterm of h1, stop pinging h4. Our goal is to create congestion on the best path of h1->h3, h1->h4 and vice versa and h1 pinging h3 is enough for that
1.	Go to your Terminal and open a new tab and run the **loadbalancer.py** script
2.	Provide input arguments such as host 1, host 2 and host 2's neighbor in integer format like for example *1,4,3* where 1 is host 1, 4 is host 2 and 3 is host 2's neighbor. Look at the topology above and you will find that these hosts are nothing but h1, h4 and h3 respectively.
3.	The loadbalancer.py performs REST requests, so initially the link costs will be 0. Re-run the script few times. This may range from 1-10 times. This is because statistics need to be enabled. After enabling statistics, it takes some time to gather information. Once it starts updating the transmission rates, you will get the best path and the flows for best path will be statically pushed to all the switches in the new best route. Here the best route is for h1->h4 and vice versa
4.	To check the flows, perform a REST GET request to http://127.0.0.1:8080/wm/core/switch/all/flow/json

VERIFICATION
1.	Now on second console of h1 type ``` ping 10.0.0.4 ```
2.	Go to wireshark and monitor interface ``` s1-eth4 ``` with the filter ``` ip.addr==10.0.0.x ``` where x is 3 and 4. You will find 10.0.0.3 packets but no 10.0.0.4 packets
3.	Stop the above capture and now do the capture on ``` s1-eth3, s21-eth1, s21-eth2, s21-eth3 ``` with the filter ``` ip.addr==10.0.0.x ``` where x is 3 and 4. You will find 10.0.0.4 packets but no 10.0.0.3 packets

RESULT
    Load Balancing Works!

SYSTEM REQUIREMENTS:
a.	    SDN Controller - Floodlight v1.2 or OpenDaylight Beryllium SR1
b.	    Virtual Network Topology - Mininet
c.	    Evaluation & Analysis - Wireshark, iPerf
d.	    OS - Ubuntu 14.04 LTS
