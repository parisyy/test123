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

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $('#start_date').datepicker({
        dateFormat: 'yy-mm-dd',
    });

    $('#end_date').datepicker({
        dateFormat: 'yy-mm-dd',
    });

    $('.chzn-select').chosen();

    new AjaxUpload('upload-btn', {
        action: '/uploader',
        data: {
            _xsrf: getCookie('_xsrf'),
        },
        onComplete: function(file, response) {
            response = JSON.parse(response);
            console.log(response["id"]);
            create_thumbnail('http://' + location.host + '/' + response["url"]);
            //$('#pic_ids').append('<input type="hidden" name="pic_ids" value="' + response["id"] + '">');
            //$('#pic_ids').append('<input type="hidden" name="pic_urls" value="' + response["url"] + '">');

            $('#pic_ids').append('<input type="hidden" name="pics" value="'
                + response["id"] + '|' + response["name"] + '">');
        },
    });
});
