The Game
========
Snowball is a "dog eat dog" game. Players maneuver a snowball across the sky,
dodging larger snowballs, in an effort to be the last snowball standing.

Preview
-------
(video coming soon)  
![alt
text](https://raw.github.com/stoneG/snowball/master/images/TWO-1.png "Two players on
Ubuntu 12.04")  
![alt
text](https://raw.github.com/stoneG/snowball/master/images/TWO-2.png "Growing larger...")  
![alt
text](https://raw.github.com/stoneG/snowball/master/images/TWO-3.png "Looks like green
didn't make it")  
![alt
text](https://raw.github.com/stoneG/snowball/master/images/THREE-1.png "Three players on
OSX 10.8")  
![alt
text](https://raw.github.com/stoneG/snowball/master/images/THREE-2.png "Stoplight
formation")  
![alt
text](https://raw.github.com/stoneG/snowball/master/images/THREE-3.png "What's gonna
happen?")

Release
-------
(0.3) Optimized some server calculations, and the game now supports up to
5 players, though YMMV depending on your network connection.  
(0.2) Multiplayer is GO.  
(0.1) Currently you can play the game as a mutant green snowball that
terrorizes all the other snowflake denizens. That's about it though.

Installation
------------
What you need to run the server: python.  
What you additionally need to run the client: pygame.  

Ubuntu:
<pre>
sudo apt-get install python-pygame
</pre>

Clone 'snowball' repository into folder of choice:
<pre>
git clone https://github.com/stoneG/snowball.git
</pre>

Running the game
----------------
First run the server. You may give a specific IP address for the server to bind
to (ie if you want to run locally) or let it automatically attach to your outward IP address.  
First, run the server.  It will automatically attach to your outward IP
address.
<pre>
python server.py
</pre>
You may also give a specific IP address instead, such as localhost:
<pre>
python server.py '127.0.0.1'
</pre>
  
Now, please note the IP address that the server is binded and listening on. For
example, '192.168.21.45' below:
<pre>
Listening at ('192.168.21.45', 1060)
</pre>
  
Then you want to run your client and point to the server's IP address.  
For example, if the server's IP is 192.168.21.45:
<pre>
python client.py '192.168.21.45'
</pre>
  
Then, you should see a client window pop up. clients connect to the server with SPACE. After all desired connections are made, the master client (designated by the server) will have the option of starting the game by hitting 's'.  

Controls
--------
ARROWS: Movement  
SPACE : Compress snowball for more speed, at the expense of size  
ESC   : Quit game

TODO
----
* Polish
* Better interface
* Scoring system/High scores
* Allow players to chat/choose snowball color/have a screenname
* Tons more
