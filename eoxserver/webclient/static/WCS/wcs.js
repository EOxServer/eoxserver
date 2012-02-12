/*
#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------
*/

(function() {
	window.WCS = function () {
		return {
			describeEOCoverageSetURL: function (baseurl, eoid, params) {
				params = params || {};
				subsetCRS = params.subsetCRS || "http://www.opengis.net/def/crs/EPSG/0/4326";
				if (baseurl.charAt(baseurl.length-1) !== "?")
					baseurl += "?";
				baseurl += "service=wcs&version=2.0.0&request=describeeocoverageset&eoid=" + eoid;
				
				if (params.bbox && !params.subsetX && !params.subsetY) {
					params.subsetX = [params.bbox[0], params.bbox[2]];
					params.subsetY = [params.bbox[1], params.bbox[3]];
				}
				if (params.subsetX) {
					baseurl += "&subset=x," + subsetCRS + "("
							+ params.subsetX[0] + "," + params.subsetX[1] + ")";
				}
				if (params.subsetY) {
					baseurl += "&subset=y," + subsetCRS + "("
							+ params.subsetY[0] + "," + params.subsetY[1] + ")";
				}
				
				if (params.subsetTime) {
				    baseurl += "&subset=phenomenonTime(\"" + params.subsetTime[0] 
				    		+ "\",\"" + params.subsetTime[1] + "\")";
				}
				if (params.containment) {
					baseurl += "&containment=" + params.containment; 
				}
				if (params.count) 
					baseurl += "&count=" + params.count;
				if (params.sections)
					baseurl += "&sections=" + params.sections;
				
				return baseurl;
			},
			getCoverageURL: function(baseurl, coverageid, format, params) {
				params = params || {};
				subsetCRS = params.subsetCRS || "http://www.opengis.net/def/crs/EPSG/0/4326";
				if (baseurl.charAt(baseurl.length-1) !== "?")
					baseurl += "?";
				baseurl += "service=wcs&version=2.0.0&request=getcoverage";
				baseurl += "&coverageid=" + coverageid + "&format=" + format;

				if (params.bbox && !params.subsetX && !params.subsetY) {
					params.subsetX = [params.bbox[0], params.bbox[2]];
					params.subsetY = [params.bbox[1], params.bbox[3]];
				}
				if (params.subsetX)
					baseurl += "&subset=x," + subsetCRS + "("
							+ params.subsetX[0] + "," + params.subsetX[1] + ")";
				if (params.subsetY)
					baseurl += "&subset=y," + subsetCRS + "("
							+ params.subsetY[0] + "," + params.subsetY[1] + ")";
				if (params.size && !params.sizeX && !params.sizeY) {
					params.sizeX = params.size[0];
					params.sizeY = params.size[1];
				}
				if (params.sizeX)
					baseurl += "&size=x(" + params.sizeX + ")";
				if (params.sizeY)
					baseurl += "&size=y(" + params.sizeY + ")";
				if (params.resolution && !params.resolutionX && !params.resolutionY) {
					params.resolutionX = params.resolution[0];
					params.resolutionY = params.resolution[1];
				}
				if (params.resolutionX)
					baseurl += "&resolution=x(" + params.resolutionX + ")";
				if (params.resolutionY)
					baseurl += "&resolution=y(" + params.resolutionY + ")";
				if (params.outputCRS)
					baseurl += "&outputcrs=" + params.outputCRS;
				if (params.multipart)
					baseurl += "&mediatype=multipart/mixed";
				
				if (params.rangeSubset)
					baseurl += "&rangesubset=" + params.rangeSubset.join(",");
				
				return baseurl;
			}
		}
	}();
}) ();
