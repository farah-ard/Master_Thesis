/**
 * Orthanc - A Lightweight, RESTful DICOM Store
 * Copyright (C) 2012-2016 Sebastien Jodogne, Medical Physics
 * Department, University Hospital of Liege, Belgium
 * Copyright (C) 2017-2023 Osimis S.A., Belgium
 * Copyright (C) 2024-2025 Orthanc Team SRL, Belgium
 * Copyright (C) 2021-2025 Sebastien Jodogne, ICTEAM UCLouvain, Belgium
 *
 * This program is free software: you can redistribute it and/or
 * modify it under the terms of the GNU Affero General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Affero General Public License for more details.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 **/


// For IE compatibility
if (!window.console) window.console = {};
if (!window.console.log) window.console.log = function () { };


// http://stackoverflow.com/a/21903119/881731
function GetUrlParameter(sParam) 
{
  var sPageURL = decodeURIComponent(window.location.search.substring(1));
  var sURLVariables = sPageURL.split('&');
  var sParameterName;
  var i;

  for (i = 0; i < sURLVariables.length; i++) {
    sParameterName = sURLVariables[i].split('=');

    if (sParameterName[0] === sParam) {
      return sParameterName[1] === undefined ? '' : sParameterName[1];
    }
  }

  return '';
};


function InitializePyramid(pyramid, tilesBaseUrl)
{
  $('#map').css('background', pyramid['BackgroundColor']);  // New in WSI 2.1

  var description = GetUrlParameter('description') || 'No description';

  var width = pyramid['TotalWidth'];
  var height = pyramid['TotalHeight'];
  var countLevels = pyramid['Resolutions'].length;

  // Maps always need a projection, but Zoomify layers are not geo-referenced, and
  // are only measured in pixels.  So, we create a fake projection that the map
  // can use to properly display the layer.
  var proj = new ol.proj.Projection({
    code: 'pixel',
    units: 'pixel',
    extent: [0, 0, width, height]
  });

  var extent = [0, -height, width, 0];

  var rotateControl = new ol.control.Rotate({
    autoHide: false,  // Show the button even if rotation is 0
    resetNorth: function() {  // Disable the default action
    }
  });

  new bootstrap.Popover(rotateControl.element, {
    placement: 'right',
    container: 'body',
    html: true,
    content: $('#popover-content')
  });

  // Disable the rotation of the map, and inertia while panning
  // http://stackoverflow.com/a/25682186
  var interactions = ol.interaction.defaults.defaults({
    //pinchRotate : false,
    dragPan: false  // disable kinetics
    //shiftDragZoom: false  // disable zoom box
  }).extend([
    new ol.interaction.DragPan(),
    new ol.interaction.DragRotate({
      //condition: ol.events.condition.shiftKeyOnly  // Rotate only when Shift key is pressed
    })
  ]);

  var controls = ol.control.defaults.defaults({
    attribution: false
  }).extend([
    rotateControl,
    new ol.control.ScaleLine({
      minWidth: 100
    }),
    new ol.control.Attribution({
      attributions: description,
      collapsible: false
    })
  ]);


  var layer = new ol.layer.Tile({
    extent: extent,
    source: new ol.source.TileImage({
      projection: proj,
      tileUrlFunction: function(tileCoord, pixelRatio, projection) {
        return (tilesBaseUrl + (countLevels - 1 - tileCoord[0]) + '/' + tileCoord[1] + '/' + tileCoord[2]);
      },
      tileGrid: new ol.tilegrid.TileGrid({
        extent: extent,
        resolutions: pyramid['Resolutions'].reverse(),
        tileSizes: pyramid['TilesSizes'].reverse()
      })
    }),
    wrapX: false,
    projection: proj,
    zIndex : 0
  });

  var styles = [
    /* We are using two different styles for the polygons:
     *  - The first style is for the polygons themselves.
     *  - The second style is to draw the vertices of the polygons.
     *    In a custom `geometry` function the vertices of a polygon are
     *    returned as `MultiPoint` geometry, which will be used to render
     *    the style.
     */
    new ol.style.Style({
      stroke: new ol.style.Stroke({
        color: '#069bff',
        width: 3,
      }),
      fill: new ol.style.Fill({
        color: 'rgba(255, 255, 255, 0.1)'
      })
    }),
    new ol.style.Style({
      image: new ol.style.Circle({
        radius: 0,
        fill: new ol.style.Fill({
          color: '#069bff'
        })
      }),
      geometry: function(feature) {
        // return the coordinates of the first ring of the polygon
        var coordinates = feature.getGeometry().getCoordinates()[0];
        return new ol.geom.MultiPoint(coordinates);
      }
    })
  ];

  

  // Vector layer for user interactions (like drawing, selecting and deleting a ROI)
  var sourceVector =  new ol.source.Vector();
  var layerVector = new ol.layer.Vector({
    source : sourceVector,
    style : styles,
    // Ensure that the drawn ROIs are always on top (arbitrary big number)
    zIndex : 99
  });


  var map = new ol.Map({
    target: 'map',
    layers: [ layer, layerVector ],
    view: new ol.View({
      projection: proj,
      center: [width / 2, -height / 2],
      zoom: 0,
      minResolution: 0.1   // "1" means "do not interpelate over pixels"
    }),
    interactions: interactions,
    controls: controls
  });

  map.getView().fit(extent, map.getSize());

  let interact = null;

  // Adding a drawing interaction to draw the ROI
  const draw = new ol.interaction.Draw({
    source: sourceVector,
    type: 'Polygon'
  });
  map.addInteraction(draw);
  draw.setActive(false);

  // Draw a ROI
  $('#draw-button').click(function() {
    draw.setActive(true);
    select.setActive(false);
    interact = draw;
  });
  
  // Adding a select interaction to select the relevant ROI
  const select = new ol.interaction.Select({
    layers: [ layerVector ],
    condition: ol.events.condition.click
  });
  map.addInteraction(select);
  select.setActive(false);

  let selectedFeatures = null;
  let roi = null;
  
  // Select ROI and get its bounding box
  $('#select-button').click(function() {
    //map.getInteractions().removeInteraction(draw);
    draw.setActive(false);
    select.setActive(true);
    interact = select;
    interact.on('select', function (e) {
      selectedFeatures = e.selected;
      if(selectedFeatures.length > 0 ){
        roi = selectedFeatures[0];
        var boundingBox = roi.getGeometry().getExtent();
        console.log(boundingBox);
        window.ROIBoundingBox = {minX : boundingBox[0], minY : boundingBox[1], maxX : boundingBox[2], maxY : boundingBox[3]};
        var boundingBoxCenter = ol.extent.getCenter(boundingBox);
        window.ROICenter = {x : boundingBoxCenter[0], y : boundingBoxCenter[1]};
        console.log(boundingBoxCenter);
      }
    });
  });

  // Delete selected ROI
  $('#delete-button').click(function() {
    if(interact instanceof ol.interaction.Select){
        const selectedFeatures = interact.getFeatures();
        if(selectedFeatures.getLength() > 0){
            const feature = selectedFeatures.item(0);
            sourceVector.removeFeature(feature);
        }
    } else {
      alert('Error - Select a region of interest to delete');
      return;
    }
  });

  let segmentationAlgo = null;
  let imageUrl;

  $('#watershed-button').click(function() {
    segmentationAlgo = 'watershed';
    if(roi != null){
      console.log('Watershed button pressed and roi is selected');
      
      console.log(imageUrl);
      var tilesExtent = getTilesCoordinates();
      pasteProcessedImage(imageUrl, tilesExtent);
      console.log("Image processed successfully and overlay added");
    } else {
      alert('Error - Select a region of interest to run the chosen algorithm');
      return;
    }
  });

  $('#stardist-button').click(function() {
    segmentationAlgo = 'stardist';
    if(roi != null){
      console.log('Stardist button pressed and roi is selected');
      getTilesCoordinates();
    } else {
      alert('Error - Select a region of interest to run the chosen algorithm');
      return;
    }
  });

  // Function to get the coordinates of the tiles of the finest level of precision that fall under the ROI drawn by the user
  function getTilesCoordinates(){
    // Get the tile grid of the image
    const tileGrid = layer.getSource().getTileGrid();
    // Get the maximum zoom level of the grid
    const maxZoom = tileGrid.getMaxZoom();
    // Get the size of the tiles and resolution at that zoom level
    const tileSizeMaxPrecision = tileGrid.getTileSize(maxZoom);
    const maxResolution = tileGrid.getResolution(maxZoom);
    // Get the bounding box of the ROI
    let roiBounds = window.ROIBoundingBox;
    // Get the coordinates of the first tile and last tile that fall under the ROI bounding box
    let minTile = tileGrid.getTileCoordForCoordAndResolution([roiBounds.minX, roiBounds.minY],maxResolution);
    let maxTile = tileGrid.getTileCoordForCoordAndResolution([roiBounds.maxX, roiBounds.maxY],maxResolution);
    // Get tiles extent to paste the processed image back on the map
    let tilesExtentMin = tileGrid.getTileCoordExtent([maxZoom, minTile[1], minTile[2]]);
    let tilesExtentMax = tileGrid.getTileCoordExtent([maxZoom, maxTile[1], maxTile[2]]);
    let tilesExtent = [tilesExtentMin[0], tilesExtentMin[1], tilesExtentMax[2], tilesExtentMax[3]];
    // Get the number of columns and rows in the region to download
    const gridSize = [minTile[2]-maxTile[2]+1, maxTile[1]-minTile[1]+1];
    // tileTable is an array that stores the coordinates of each tile in the region to download
    let tileTable = [];
    // Loops to fill tileTable
    for (let x = maxTile[2]; x <= minTile[2]; x++) {
      let rowTiles = [];
      for (let y = minTile[1]; y <= maxTile[1]; y++){
        rowTiles.push([x,y]);
      }
      tileTable.push(rowTiles);
    }
    console.log(tileTable);
    imageUrl = getTilesFromOrthanc(tileTable,tileSizeMaxPrecision, gridSize, segmentationAlgo, tilesExtent);
    return tilesExtent;
  }

  
  const olSourceRasterOperation = pixels => {
    if (pixels[1][3] === 0) {
      return [0,0,0,0];
    } else {
      return pixels[0];
    }
  };  

  function pasteProcessedImage(imageUrl, tilesExtent){
    // Source https://chrishewett.com/blog/combining-openlayers-raster-and-vector-layers-for-cropping-and-masking/?
    // Add the overlay layer to the map
    const olLayerImage = new ol.layer.Image({
      source: new ol.source.Raster({
        sources: [
          new ol.source.ImageStatic({
            url: imageUrl,
            imageExtent: tilesExtent,
            projection: proj
          }),
          layerVector
        ],
        operation: olSourceRasterOperation
      }),
      zIndex : 1
    });
    map.addLayer(olLayerImage);
  }


  $('#rotation-slider').on('input change', function() {
    map.getView().setRotation(this.value / 180 * Math.PI);
  });
  $('#rotation-reset').click(function() {
    $('#rotation-slider').val(0).change();
  });
  $('#rotation-minus90').click(function() {
    var angle = parseInt($('#rotation-slider').val()) - 90;
    if (angle < -180) {
      angle += 360;
    }
    $('#rotation-slider').val(angle).change();
  });
  $('#rotation-plus90').click(function() {
    var angle = parseInt($('#rotation-slider').val()) + 90;
    console.log(angle);
    if (angle > 180) {
      angle -= 360;
    }
    $('#rotation-slider').val(angle).change();
  });
}

// $ is a shortcut for jQuery
//A page can't be manipulated safely until the document is "ready." jQuery detects this state of readiness for you. 
// Code included inside $( document ).ready() will only run once the page Document Object Model (DOM) is ready for JavaScript code to execute.
$(document).ready(function() {
  var seriesId = GetUrlParameter('series');

  if (seriesId.length != 0) {
    $.ajax({
      url : './orthanc/pyramids/' + seriesId,
      error: function() {
        alert('Error - Cannot get the pyramid structure of series: ' + seriesId);
      },
      success : function(pyramid) {
        InitializePyramid(pyramid, './orthanc/tiles/' + seriesId + '/');
      }
    });
  } else {
    alert('Error - No series ID is specified!');
  }
});

function getTilesFromOrthanc(tileTable, tileSize, gridSize, algo, tilesExtent){
  var seriesId = GetUrlParameter('series');
  $.ajax({
    url : '/download_tiles',
    type: 'POST',
    // Sending data as json
    contentType : 'application/json',
    // The kind of response to expect
    dataType: 'json',
    data : JSON.stringify({
      seriesId : seriesId,
      tileTable : tileTable,
      tileSize : tileSize,
      gridSize : gridSize,
      algo : algo
    }),
    async : false,
    success : function(response){
      console.log('success');
      imageUrl = response.image_url;
    },
    error: function(xhr, status, error) {
      console.error("AJAX Error: ", status, error);
      console.log("Response Text:", xhr.responseText);
      console.log("Response Status:", xhr.status);
    },
  });
  return imageUrl;
}


