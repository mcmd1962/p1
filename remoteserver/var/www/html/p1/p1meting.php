 <!DOCTYPE HTML>
 <html>
 <head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta http-equiv="refresh" content="300"> <!-- reload page every 5 minutes !-->
  <title>Energieverbruik 2 weken</title>
  <?php
  $link = pg_connect("host=localhost port=5432 dbname=p1_readings user=meteruserro password=password connect_timeout=15") or die("Error verbinden met DB");

// Alle waardes ophalen voor huidig verbruik. Query haalt nu alle resultaten op. Met 'DATE_SUB' in query kunnen waarden beperkt worden.
#$result = pg_exec($link, "SELECT extract(epoch from  time) AS ts, time, gemiddeld_verbruik AS sensor_1 FROM readings WHERE time >= current_date - integer '7'  order by time;");
$result = pg_exec($link, "SELECT extract(epoch from  time) AS ts, time, gemiddeld_verbruik AS sensor_1 FROM readings WHERE time >= current_date - integer '28'  order by time;");
 if (!$result) {
  pg_close($link);
  die("Error met query gemiddeld verbruik: ");
}
// echo("result\n");
// print_r($result);
while ($row = pg_fetch_array($result)) {
  // echo("row\n");
  // print_r($row);
  $datetime = (($row['ts']) * 1000) ; // convert from Unix timestamp to JavaScript time
  $latest_measure = $row['time'];
  $value1   = $row['sensor_1'];
  $data1[] = "[$datetime, $value1]";

}

// echo("data_1\n");
// print_r($data_1);
$data_1 = join($data1, ',');
//print_r($data_1);

?>

<script type="text/javascript" src="js/jquery-latest.js"></script>
<script type="text/javascript">
$(function () {
  $('#container').highcharts('StockChart',  {
    chart: {
      zoomType: 'x'
    },
    navigator: {
      enabled: true,
      outlineWidth: 2
    },
    rangeSelector: {
      enabled: true,
      buttons: [
                { type: 'hour',  count:  4, text: '4h' }, 
                { type: 'hour',  count: 12, text: '12h' }, 
                { type: 'day',   count:  1, text: '1d' }, 
                { type: 'day',   count:  4, text: '4d' }, 
                { type: 'week',  count:  1, text: '1w' }, 
                { type: 'week',  count:  2, text: '2w' }, 
                { type: 'all', text: 'All' }
               ],
      selected: 1
    },
    title: {
      text: 'Energieverbruik via slimme meter'
    },
    subtitle: {
      text: document.ontouchstart === undefined ?
        'Klik en sleep in de grafiek om in te zoomen' :
        'Maak een knijpbeweging om in te zoomen' //only shown on touch (tablet) devices
    },
    xAxis: {
          type: 'datetime',
      minRange: 10 * 1000 // Smallest zoominterval (in miliseconds). 10 * 1000 = 10.000ms
                          // because smartmeter spits out data every 10sec.
    },
    yAxis: {
      min: 0,    // Schaal instellen, uncomment de min en max voor automatisch
      //max: 80,
      title: {
        text: 'Verbruik in Watt (W)'
      }
    },
    tooltip: {
      valueSuffix: 'W'
    },
    legend: {
      layout: 'vertical',
      align: 'right',
      verticalAlign: 'middle',
      borderWidth: 0
    },
    plotOptions: {
      area: {
        fillColor: {
          linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1},
          stops: [
            [0, Highcharts.getOptions().colors[0]],
            [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
          ]
        },
        marker: {
          radius: 2
        },
        lineWidth: 1,
        states: {
          hover: {
            lineWidth: 1
          }
        },
        threshold: null
      }
    },
    legend: {
      enabled: false
    },
    series: [{
      name: 'Verbruik',
      color: '#f3c629',
      marker: {
        enabled: false
      },
      data: [<?php
        echo ($data_1);
      ?>]
    },
    ]

  });
});
<?php
// Nieuwste enkele waarde voor huidig_verbruik ophalen
$result = pg_exec($link, "SELECT id as LATEST, gemiddeld_verbruik FROM readings ORDER BY id DESC LIMIT 1");
if (!$result) {
  pg_close($link);
  die("Error met query: enkele waarde huidig verbruik");
}
while ($row = pg_fetch_array($result)) {
  $huidig_verbruik = $row['gemiddeld_verbruik'];
}

?>


</script>
<style type="text/css">
body {
  background-color: #FFFFFF;
  font-family: 'Helvetica, Arial, sans-serif';
  color: black;
  font-size: 20px;
  text-align: center;
}
p {
  font-family: 'helvetica, arial, sans-serif';
}
</style>
</head>
<body>
  <!-- <script src="js/highcharts.js"></script>  -->
  <script src="js/highstock.js"></script>
  <script src="js/modules/exporting.js"></script>

  <div id="container" style="min-width: 310px; height: 400px; margin: 0 auto"></div>
  <p style="font-family:helvetica, tahoma, sans-serif;">
    <span style="color: #000000";>Actueel:</span> <br />
    <span style="color: #f3c629";>&nbsp;Huidig verbruik: <?php echo (number_format($huidig_verbruik, 0)); ?> W</span><br />
    <br />
    <span style="color: #000000";><font size="2">Laatste meting opgehaald om:</span> <br /> <?php echo $latest_measure; ?></font><br>
</p>

<?php
pg_close($link);
?>

</body>
</html>
