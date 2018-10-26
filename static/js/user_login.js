$(function(){
    //嵌入验证码
    var handlerEmbed = function(captchaObj) {
        $("#embed-submit").click(function(e) {
            var validate = captchaObj.getValidate();
            if(!validate) {
                $("#notice")[0].className = "show";
                setTimeout(function() {
                    $("#notice")[0].className = "hide";
                }, 2000);
                e.preventDefault();
            }
        });
        // 将验证码加到id为captcha的元素里，同时会有三个input的值：geetest_challenge, geetest_validate, geetest_seccode
        $("#embed-captcha").empty();
        captchaObj.appendTo("#embed-captcha");
        captchaObj.onReady(function() {
            $("#wait")[0].className = "hide";
        });
        // 更多接口参考：http://www.geetest.com/install/sections/idx-client-sdk.html
    };

    //获取验证码参数的函数
    function get_geetest_code(){
        $.ajax({
            // 获取id，challenge，success（是否启用failback）
            url: "/user/geetest/register?t=" + (new Date()).getTime(), // 加随机数防止缓存
            type: "get",
            dataType: "json",
            success: function(data) {
                // 使用initGeetest接口
                // 参数1：配置参数
                // 参数2：回调，回调的第一个参数验证码对象，之后可以使用它做appendTo之类的事件
                initGeetest({
                    gt: data.gt,
                    width: '100%',
                    challenge: data.challenge,
                    product: "embed", // 产品形式，包括：float，embed，popup。注意只对PC版验证码有效
                    offline: !data.success // 表示用户后台检测极验服务器是否宕机，一般不需要关注
                    // 更多配置参数请参见：http://www.geetest.com/install/sections/idx-client-sdk.html#config
                }, handlerEmbed);
            }
        });
    }
    get_geetest_code();

    $("form input:not('#submit')").focus(function() {
        $(this).parent().find('span.icon-font').css({"color": "#56afe1", "opacity": '1'});
        $("#login_tip").css("display", "none");
    }).blur(function() {
        $(this).parent().find('span.icon-font').css({"color": "", "opacity": '0.5'});
    });

    //登录方式选择样式
    $("#nav a:first").click(function() {
        $(this).css("color", "#65c17a");
        $("#nav a:last").css("color", "#333");
        $(".hidden").css("display", "none");
        $('#childuser').val('');
    });
    $("#nav a:last").click(function() {
        $(this).css("color", "#65c17a");
        $("#nav a:first").css("color", "#333");
        $(".hidden").css("display", "block");
    });

    var reg = /^([a-zA-Z0-9]|[._]){1,18}$/;

    //提交登录信息
    $('#submit').click(function(e){
        e.preventDefault();
        var l = Ladda.create(this);
        l.start();
        $("#login_tip").css("display", "none");
        var username = $("#username").val();
        var childuser = '';
        var password = $("#password").val();
        if(username === "" || username === null) {
            error_handler(l, '账号邮箱错误');
            return
        }
        if($(".hidden").css("display") === "block") {
            var get_account = $("#childuser").val();
            if(get_account === "" || get_account === null || !reg.test(get_account)) {
                error_handler(l, '子账号错误');
                return
            }
            else{
                childuser = get_account;
            }
        }
        if(password === "" || password === null){
            error_handler(l, '密码错误');
            return
        }
        var secure_password = md5(password);
        post_user_data(username, childuser, secure_password, l);
    });

    //提交处理
    function post_user_data(username, sub_account, password, l) {
        var geetest_challenge = $('input[name="geetest_challenge"]').val(),
            geetest_validate = $('input[name="geetest_validate"]').val(),
            geetest_seccode = $('input[name="geetest_seccode"]').val();
        var post_data = {
            'user_email': username,
            'sub_account': sub_account,
            'password': password,
            'geetest_challenge': geetest_challenge,
            'geetest_validate': geetest_validate,
            'geetest_seccode': geetest_seccode
        };
        $.post('/user/login', post_data, function(res){
            if(res.success===1){
                location.href='/';
            }
            else{
                error_handler(l, res['err_msg']);
            }
        })
    }

    function error_handler(l, msg){
        l.stop();
        $("#embed-captcha").empty();
        $("#wait")[0].className = "show";
        $("#login_tip").css("display", "block").find('span').html(msg);
        get_geetest_code();
    }



    var ego_request_interval = null;
    var ego_request_timeout = null;
    var qr_url = '';

    $('#ego-login').click(function () {
        get_qr_code();
        $('#form_content').hide();
        $('#ego-login-demo').show();
        $('#ego-login').parent().hide();
        $('#password-login').parent().show();
        ego_request_interval = setInterval(get_login_result, 1000);
        ego_request_timeout = setTimeout(function () {
            clearInterval(ego_request_interval);
            $('#ego-login-demo').find('p').slice(1,2).show();
            $('#ego-qrcode').css('opacity', 0.5)
        }, 60000)

    });

    $('#password-login').click(function () {
        $(this).parent().hide();
        $('#ego-login-demo').hide();
        $('#form_content').show();
        $('#ego-login').parent().show();
        clearInterval(ego_request_interval);
        clearTimeout(ego_request_timeout);
    });
    $('#refresh-qr').click(function () {
        get_qr_code();
        $('#ego-qrcode').css('opacity', 1);
        $('#ego-login-demo').find('p').slice(1,2).hide();
        ego_request_interval = setInterval(get_login_result, 1000);
        ego_request_timeout = setTimeout(function () {
            clearInterval(ego_request_interval);
            $('#ego-login-demo').find('p').slice(1,2).show();
            $('#ego-qrcode').css('opacity', 0.5)
        }, 60000)
    });
    function get_login_result() {
        $.ajax({
            url: '/user/get_result?'+qr_url.split('?')[1],
            type: 'GET',
            success: function (res) {
                if(res.status === 1){
                    if(res.login_status === 'login'){
                        window.location.href = '/user/login_success';
                    }else{
                        console.log(1)
                        $('#ego-qrcode').html('<p style="color: red;font-size: 20px">请在APP上确认授权</p>');
                    }
                }
            }
        });
    }
    function get_qr_code() {
        $('#ego-qrcode').empty();
        $.ajax({
            url: '/user/get_qr_code',
            type: 'GET',
            success: function (res) {
                if(res.status === 1){
                    var ego_qrcode = new QRCode('ego-qrcode');
                    ego_qrcode.makeCode(res.url);
                    qr_url = res.url;
                }else{

                }
            }
        });
    }
});