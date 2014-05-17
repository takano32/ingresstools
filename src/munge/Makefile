munge.json: munge.js
	umask 066
	phantomjs mungeextract.js

munge.js:
	wget https://raw.githubusercontent.com/jonatkins/ingress-intel-total-conversion/master/code/munge.js


clean:
	rm -f munge.js
	rm -f munges.json
	rm -f cookies.json

