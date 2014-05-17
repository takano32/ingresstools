#!/usr/bin/env phantomjs
// -*- coding: utf-8 -*-
// vim: ts=4 sw=4 sts=4 ff=unix expandtab

var page = require('webpage').create();
var fs = require('fs');

page.customHeaders = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.99 Safari/537.36"
};

page.onInitialized = function(){
    page.evaluate(function(){
        document.addEventListener('DOMContentLoaded', function(){
            window.callPhantom('DOMContentLoaded');
        }, false);
    });
};

var funcs = function(funcs){
    this.funcs = funcs;
    this.init();
};


funcs.prototype = {
    init: function(){
        var self = this;
        page.onCallback = function(data){
            if(data === 'DOMContentLoaded') self.next();
        }
    },
    next: function(){
        var func = this.funcs.shift();
        if(func !== undefined){
            func();
        }else{
            page.onCallback = function(){};
        }
    }
};




new funcs([
    function(){
        // login to google
        console.log("1");
        page.open("https://accounts.google.com/ServiceLogin?");
    },
    function(){
        // fillin ID/Password
        console.log("2");
        if(! phantom.injectJs("auth.js")){
            console.log("can't read auth.js, please specify id/password to auth.js");
            phantom.exit(1);
        }
        page.evaluate(function(auth){
            document.getElementById("Email").value = auth.id;
            document.getElementById("Passwd").value = auth.password;
            document.querySelector("form").submit();
        }, auth);
    },
    function(){
        // force move to intel map
        console.log("3");
        page.open('https://ingress.com/intel');
    },
    function(){
        // sometimes this page has come, I can't figure out
        console.log("4");
        page.evaluate(function(){
            var ev = document.createEvent('MouseEvents');
            ev.initEvent('click', false, true);
            document.getElementsByTagName('a')[0].dispatchEvent(ev);
            return document.getElementsByTagName('html')[0].innerHTML;
        });
    },
    function(){
        // intel map
        console.log("5");
        page.open('https://ingress.com/intel', function(){
            if(! page.injectJs("./munge.js")){
                console.log("can't injectJs munge.js");
                phantom.exit(1);
            }
            var munges = page.evaluate(function() {
                var munges = {};
                var mungeNames = ["ascendingTimestampOrder", "chatTabGet", "chatTabSendPlext", "dashboard.getArtifactInfo", "dashboard.getGameScore", "dashboard.getPaginatedPlexts", "dashboard.getPortalDetails", "dashboard.getThinnedEntities", "dashboard.sendPlext", "desiredNumItems", "guid", "latE6SendPlext", "lngE6SendPlext", "maxLatE6", "maxLngE6", "maxTimestampMs", "messageSendPlext", "method", "minLatE6", "minLngE6", "minTimestampMs", "quadKeys", "version", "version_parameter"];
                for(var i=0; i<mungeNames.length; i++){
                    try {
                        munges[mungeNames[i]] = mungeOneString(mungeNames[i]);
                    } catch(e) {
                        return "Error:" + e.error + " Line:" + e.line + " Source:" + e.sourceURL;
                    }
                }
                return munges;
            });
            console.log("munges =>", JSON.stringify(munges, null, "  "));
            fs.write("munges.json", JSON.stringify(munges, null, "  "), 'w');
            fs.write("cookies.json", JSON.stringify(phantom.cookies, null, "  "), 'w');
            phantom.exit(0);
        });
    }
]).next();
