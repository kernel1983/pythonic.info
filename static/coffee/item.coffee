
$ ->
    feed_status_template = _.template($('#feed-status-template').html())
    feed_comment_template = _.template($('#feed-comment-template').html())

    $.getJSON "/api/get_item?id="+ITEM_ID, (data) ->
        $("#feeds").empty()

        feed_data = data["item"]
        user_id = feed_data["user_id"]

        feed_data["user"] = data["users"][user_id]
        feed_data["url"] = feed_data["url_cn"] or feed_data["url_en"]
        feed_data["like"] = _.indexOf(feed_data["likes"], my_user_id) > -1

        insert_feed(feed_data, data["users"])

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

        feed = $("#feed-"+feed_data["id"])
        for j in feed_data["comments"] or []
            comment_data = j
            user_id = comment_data["user_id"]

            comment_data["user"] = users[user_id]
            comment_data["like"] = comment_data["likes"].indexOf(my_user_id) > -1

            feed.append(feed_comment_template(comment_data))
            insert_feed(comment_data, users)

    $("#open_help").click () -> $("#help_panel").show()
    $("#close_help").click () -> $("#help_panel").hide()

    $("abbr.timeago").timeago()
