function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function popup_alert(element, callback) {
    $(element).dialog({
        autoopen: false,
        model: true,
        buttons: {
            '确定': function() {
                callback();
                $(this).dialog('close');
            },
            '取消': function() {
                $(this).dialog('close');
            },
        },
    });
}

function set_region_selectors() {
    // 动态更新城市列表
    $('#province_id').change(function(e) {
        if ($('#province_id').val() == '') {
            return ;
        }

        $.ajax({
          url: '/region',
          type: 'GET',
          data: { type: 4, region_id: $('#province_id').val() },
          success: function(data) {
            cities = JSON.parse(data);
            if (cities['code'] == 0) {
              var i;
              $('#city_id').empty();
              $("#city_id").append('<option></option>');
              for (i = 0; i < cities["data"].length; ++i) {
                $("#city_id").append('<option value="' + cities["data"][i]["id"] + '">' 
                  + cities["data"][i]["region_name"] + '</option>');
                $('.chzn-select#city_id').val('').trigger('liszt:updated');
              }
            } else {
              alert(cities['error']);
            }
          }
        });
    });
    // 动态更新区域列表
    $('#city_id').change(function(e) {
      if ($('#city_id').val() == '') {
        return ;
      }

      $.ajax({
          url: '/region',
          type: 'GET',
          data: { type: 5, region_id: $('#city_id').val() },
          success: function(data) {
            domains = JSON.parse(data);
            if (domains['code'] == 0) {
              var i;
              $('#domain_id').empty();
              $("#domain_id").append('<option></option>');
              for (i = 0; i < domains["data"].length; ++i) {
                $("#domain_id").append('<option value="' + domains["data"][i]["id"] + '">' 
                  + domains["data"][i]["region_name"] + '</option>');
                $('.chzn-select#domain_id').val('').trigger('liszt:updated');
              }
            } else {
              alert(cities['error']);
            }
          }
        });
    });
}
