 <!DOCTYPE HTML>
 <html>
 <head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta http-equiv="refresh"      content="300"> <!-- reload page every 5 minutes !-->
  <title>Energieverbruik jaar</title>

  <?php
   $link = pg_connect("host=localhost port=5432 dbname=p1_readings user=meteruserro password=password connect_timeout=15") or die("Error verbinden met DB");

   // Alle waardes ophalen voor huidig verbruik. Query haalt nu alle resultaten op. Met 'DATE_SUB' in query kunnen waarden beperkt worden.
   $result = pg_exec($link, "SELECT ceil(
               ( extract(epoch from  date_trunc('hour', time) )  +  3600 )  /  21600
              ) * 21600 AS ts,
           min(meterstand) AS sensor_1
   FROM readings
   GROUP BY ts
   ORDER BY ts;");

   if (!$result) {
     pg_close($link);
    die("Error met query gemiddeld verbruik: ");
   }
   $prevvalue = -1;
   $daydata = array();

   while ($row = pg_fetch_array($result)) {
     $datetime = (($row['ts']) * 1000) - 86400000; // convert from Unix timestamp to JavaScript time
     $value1   = $row['sensor_1'];
     $delta    = sprintf("%0.2f", ($value1 - $prevvalue) / 1000);
     if ( $prevvalue > 0 ) {
       $data1[] = "[$datetime, $delta]";
     }
     $prevvalue = $value1;
   }

   $data_1 = join($data1, ',');

?>

<script type="text/javascript" src="js/jquery-latest.js"></script>
<script type="text/javascript">
$(function () {
  $('#container').highcharts('StockChart',  {
    chart: {
      alignTicks: false
    },
    rangeSelector: {
      enabled: true,
      buttons: [
                { type: 'week',  count:  1, text: '1w' }, 
                { type: 'week',  count:  2, text: '2w' }, 
                { type: 'month', count:  1, text: '1m' }, 
                { type: 'month', count:  3, text: '3m' }, 
                { type: 'month', count:  6, text: '6m' }, 
                { type: 'ytd',              text: 'YTD'}, 
                { type: 'year',  count:  1, text: '1y' }, 
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
    tooltip: {
      valueSuffix: 'KWh',
      changeDecimals: 2,
    },
    legend: {
      enabled: false
    },
    series: [{
      name: 'Verbruik',
      changeDecimals: 2,
      type: 'column',
      color: '#f3c629',
      dataGrouping: {
		    groupPixelWidth: 100,
                    units: [
                        ['hour',  [6] ], 
                        ['day',   [1] ], 
                        ['week',  [1] ], 
                        ['month', [1, 2, 3, 4, 6] ]
                    ]
      },
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
    <!-- <span style="color: #000000";><font size="2">Laatste meting opgehaald om:</span> <br /> <?php echo $latest_measure; ?></font><br> -->
</p>

<?php
pg_close($link);
?>

</body>
</html>
