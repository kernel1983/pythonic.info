$ ->
    $("#feeds").on "click", ".like", () ->
        id = $(this).attr("id").slice(-32)

        $.post "/api/like", {"id":id}, (data) ->
            # alert("like success, please reload the page")
            $("#like-"+id).hide()
            $("#unlike-"+id).show()
            $("#like-count-"+id).text(data["like_count"])

    $("#feeds").on "click", ".unlike", () ->
        id = $(this).attr("id").slice(-32)

        $.post "/api/unlike", {"id":id}, (data) ->
            # alert("unlike success, please reload page")
            $("#unlike-"+id).hide()
            $("#like-"+id).show()
            $("#like-count-"+id).text(data["like_count"])

