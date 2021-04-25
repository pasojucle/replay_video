$(document).ready(function() {
    $(document).on('change', '.switch', wifiRefresh);
    $(document).on('click', '.btn-video', actionVideo);
    $(document).on('click', '#shut-down-btn', shutDown);
    $(document).on('click', '#video-reload', videoReload);
    $(document).on('click', '#ws-video-list', getVideoList);
    $('.select2-single').select2({
        language: "fr",
        ajax: {
            type: 'POST',
            delay: 250,
            data: function (params) {
              var queryParameters = {
                term: params.term
              }
              return queryParameters;
            },
            dataType: 'json'
        },
        createTag: function (params) {
            return {
              id: "#" + params.term,
              text: "#" + params.term,
              value: "#" + params.term,
              newOption: true
            }
        }
    });
    $('.status-download').each(function() {
        getStatus($(this).data('video-id'))
    });
    if ($('#videos-status-container').length > 0) {
        getVideosStatus();
    }
});

function getStatus(videoId) {
    $.ajax({
        method: "POST",
        url: "/video/show/"+videoId,
        data: { video_id: videoId},
        dataType: 'json',
    })
    .done(function( response ) {
        $('#video_detail').replaceWith(
            $(response.render).find('#video_detail')
        )
        if (response.status < 1) {
            download(videoId)
        }
        if (response.status < 2) {
            setTimeout(function(){getStatus(videoId);}, 15000);
        }
        if (response.status == 2) {
            $('#video-player-panel').removeClass('hidden');
        }
    });
}

function getVideosStatus(is_video_list_processing=false) {
    $.ajax({
        method: "GET",
        url: "/videos/status/",
        dataType: 'json',
    })
    .done(function( response ) {
        $('#videos-status-container').replaceWith(
            $(response.render)
        )
        if (response.is_video_list_processing || is_video_list_processing) {
            setTimeout(function(){getVideosStatus();}, 15000);
        }
    });
}

function getVideoList(e) {
    e.preventDefault();
    getVideosStatus(true);
    $.ajax({
        method: "GET",
        url: "/ws/video/list/ajax",
        dataType: 'json',
    })
}
function download(videoId) {
    $.ajax({
        method: "POST",
        url: "/video/download/ajax",
        data: { video_id: videoId},
        dataType: 'json',
    });
}

function wifiRefresh() {
    let target = $(this).find('input[type="checkbox"]');
    data = {};
    data[target.prop('name')] = (target.is(':checked')) ? true : false;
    $.ajax({
        method: "POST",
        url: "/network/edit",
        data: data,
        dataType: 'json',
    })
    .done(function( response ) {
        target.parents('.form-group-container').replaceWith(
            $(response.render).find('#'+target.attr('id')).parents('.form-group-container')
        )
    });
}

function actionVideo(e) {
    e.preventDefault();
    const route = $(this).prop('href');
    $('.btn-video').addClass('disabled');
    $.ajax({
        method: "POST",
        url: route,
        dataType: 'json',
    })
    .done(function( response ) {
        $('.btn-video').removeClass('disabled');
        if (response.result == 1) {
            $('.video-player a').removeClass('active');
            if (response.target) {
                $(response.target).addClass('active');
            }
        }
    });
}

function shutDown(e) {
    e.preventDefault();
    $(this).addClass('active');
    $('#videoList').addClass('hidden');
    $('#reload').removeClass('hidden');
    const route = $(this).prop('href');
        $.ajax({
        method: "POST",
        url: route,
        dataType: 'json',
    });
}

function videoReload(e) {
    e.preventDefault();
    const route = $(this).prop('href');
        $.ajax({
        method: "POST",
        url: route,
        dataType: 'json',
    });
}