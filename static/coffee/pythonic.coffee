$ ->
    $("#feeds").on "click", ".like, .count-like", () ->
        id = $(this).attr("id").slice(-32)

        $.post "/api/like", {"id":id}, (data) ->
            # alert("like success, please reload the page")
            $("#like-"+id).hide()
            $("#unlike-"+id).show()
            $("#count-like-"+id).hide()
            $("#count-unlike-"+id).show()
            $("#count-unlike-"+id+" span").text(data["like_count"])

    $("#feeds").on "click", ".unlike, .count-unlike", () ->
        id = $(this).attr("id").slice(-32)

        $.post "/api/unlike", {"id":id}, (data) ->
            # alert("unlike success, please reload page")
            $("#unlike-"+id).hide()
            $("#like-"+id).show()
            $("#count-unlike-"+id).hide()
            $("#count-like-"+id).show()
            $("#count-like-"+id+" span").text(data["like_count"])

    $("abbr.timeago").timeago();
