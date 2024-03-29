/* 上传图片 */
function upload_subject_file(element, callback) {
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

/* 上传沙龙图片 */
function upload_salon(element, id, callback) {
    new AjaxUpload(element, {
        action: '/salon_uploader',
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

/* 上传发型包zip文件 */
function upload_hairpackage(element, pkg_id, callback) {
    new AjaxUpload(element, {
        action: '/hairpackage_uploader',
        data: {
            _xsrf: getCookie('_xsrf'),
            package_id: pkg_id,
        },
        onComplete: function(file, response) {
            response = JSON.parse(response);
            if (response["code"] == 0) {
                callback(file, response);
            } else {
                alert(response["error"] + '\n\n上传发型包失败！');
            }
        }
    });
}

/* 上传发行包图片 */
function upload_hairpackage_pic(element, pkg_id, pic_type, callback) {
    new AjaxUpload(element, {
        action: '/hairpackage_pic_uploader',
        data: {
            _xsrf: getCookie('_xsrf'),
            package_id: pkg_id,
            pic_type: pic_type,
        },
        onComplete: function(file, response) {
            response = JSON.parse(response);
            if (response["code"] == 0) {
                callback(file, response);
            } else {
                alert(response["error"] + '\n\n上传发型包失败！');
            }
        }
    });
}
