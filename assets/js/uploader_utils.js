function create_thumbnail(src) {
    // 创建缩略图模块
    $('#thumbnail-snippet img').attr('src', src);
    $('#thumbnails').append($('#thumbnail-snippet').html());

    // 缩略图的点击预览
    $('.thumbnail img').click(function(event) {
        $('#image-preview img').attr('src', $(this).attr('src'));
        $('#image-preview').dialog({
            title: '图片预览',
        });
    });
}

function upload_file(element, callback) {
    new AjaxUpload(element, {
        action: '/subject_uploader',
        data: {
            _xsrf: getCookie('_xsrf'),
        },
        onComplete: function(file, response) {
            response = JSON.parse(response);
            if (response["code"] == 0) {
                callback(file, response);
            } else {
                alert(response["error"] + '\n\n上传图片失败！');
            }
        },
    });
}

function upload_callback(file, response) {
    create_thumbnail('http://' + location.host + response["url"]);
    $('#pic_ids').append('<input type="hidden" name="pics" value="'
        + response["id"] + '|' + response["name"] + '">');
}

function set_default_values() {
    $('#start_date').datepicker({
        dateFormat: 'yy-mm-dd',
    });

    $('#end_date').datepicker({
        dateFormat: 'yy-mm-dd',
    });

    $('.chzn-select').chosen();
}

$(document).ready(function() {
    set_default_values();
    upload_file('upload-btn', upload_callback);
});
