/* 上传图片 */
function upload_file(element, callback) {
    new AjaxUpload(element, {
        action: '/uploader',
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

/* 上传用户头像 */
function upload_avatar(element, uid, callback) {
    new AjaxUpload(element, {
        action: '/avatar_uploader',
        data: {
            _xsrf: getCookie('_xsrf'),
            uid: uid,
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

/* 上传沙龙LOGO */
function upload_salon_logo(element, id, callback) {
    new AjaxUpload(element, {
        action: '/salon_logo_uploader',
        data: {
            _xsrf: getCookie('_xsrf'),
            salon_id: id,
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

