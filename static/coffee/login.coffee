validateEmail = (email) ->
    re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
    return re.test(email)

$ ->
    $("#user,#password").keyup () ->
        user = $("#user").val()
        password = $("#password").val()
        if((user!="") && (password!=""))
            $.getJSON "/api/login?login="+encodeURIComponent(user), (data) ->
                if(_.has(data, "error"))
                    $("#login").addClass("disabled")
                else
                    $("#login").removeClass("disabled")
        else
            $("#login").addClass("disabled")

    $("#login").click () ->
        user = $("#user").val()
        password = $("#password").val()
        $.post "/api/login", {"login": user, "password": password}, () ->
            window.location="/"

    $("#open_help").click () -> $("#help_panel").show()
    $("#close_help").click () -> $("#help_panel").hide()
