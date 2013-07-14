
$ ->
    feed_status_template = _.template($('#feed-status-template').html())

    $.getJSON "/api/get_feed", (data) ->
        $("#feeds").empty()

        more_id = null
        for i in data["feeds"]
            feed_data = i
            user_id = feed_data["user_id"]
            more_id = feed_data["id"]

            feed_data["user"] = data["users"][user_id]
            feed_data["like"] = feed_data["likes"].indexOf(my_user_id) > -1

            insert_feed(feed_data, data["users"])

        $("#feeds").append('<a href="/?from=' + more_id + '">More</a>')
        $("abbr.timeago").timeago()

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

    insert_feed = (feed_data, users) ->
        if(feed_data["type"]=="status")
            $("#feeds").append(feed_status_template(feed_data))


    $("abbr.timeago").timeago()
