# d3.Timeslider

d3.Timeslider is a time slider based on the [D3.js](http://d3js.org) javascript
library. It is written in [CoffeeScript](http://coffeescript.org) and
[Less](http://lesscss.org)

The software is licensed under a MIT compatible license, for more information see
[License](License).

For a list of recent changes, please see the [Changelog](Changelog).

## Usage

Include the JavaScript and CSS files (and [D3.js](http://d3js.org/) as
D3.Timeslider depends on it) and then instantiate a new slider like in the
following snippet.

You can download the latest version of D3 directly from
[d3js.org/d3.v3.zip](http://d3js.org/d3.v3.zip)

```html
<!-- TimeSlider -->
<script src="build/d3.timeslider.js"></script>
<link href="build/d3.timeslider.css" rel="stylesheet" type="text/css" media="all" />
<script>
  window.addEventListener('load', function() {
    // Initialize the TimeSlider
    slider = new TimeSlider(document.getElementById('d3_timeslider'), {
      domain: {
        start: new Date("2012-01-01T00:00:00Z"),
        end: new Date("2013-01-01T00:00:00Z"),
      },
      brush: {
        start: new Date("2012-01-05T00:00:00Z"),
        end: new Date("2012-01-10T00:00:00Z")
      },
      datasets: [
        {
          id: 'img2012',
          color: 'red',
          data: function(start, end) {
            return [
              [ new Date("2012-01-01T12:00:00Z"), new Date("2012-01-01T16:00:00Z") ],
              [ new Date("2012-01-02T12:00:00Z"), new Date("2012-01-02T16:00:00Z") ],
              [ new Date("2012-01-04T00:00:00Z") ],
              [ new Date("2012-01-05T00:00:00Z"), new Date("2012-01-06T00:00:00Z") ],
              [ new Date("2012-01-06T12:00:00Z"), new Date("2012-01-26T16:00:00Z") ],
            ]
          }
        }
      ]
    });

    // Register a callback for changing the selected time period
    document.getElementById('d3_timeslider').addEventListener('selectionChanged', function(e){
      console.log("Custom event handler on the time slider");
      console.log(e.detail);
    });
  }, false);
</script>
```

## Development

Install development dependencies, and start grunt via the following two commands.

```sh
npm install
grunt watch
```

You can then open the [preview](preview.html) page and any changes to the
CoffeeScript and Less files will be automatically compiled and reloaded in the
browser.

To lint the CoffeeScript source run the following command.

```sh
grunt lint
```
