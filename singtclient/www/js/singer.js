// Create single namespace
window.SINGT = {};


SINGT.wireup = function(){
    // All wireup goes here
    SINGT.wireup.nav();
    SINGT.wireup.forms();
    SINGT.wireup.page_setup();
    SINGT.wireup.page_connect();
    SINGT.wireup.page_debug();
}

SINGT.wireup.nav = function() {
    $('.navbar-nav .nav-link').each(function(index){
        $(this).bind('click', function(){
            //change classes of nav buttons
            $('.navbar-nav .nav-item').removeClass('active');
            $(this).parent().addClass('active');
            //hide other pages show target page
            var target_id = $(this).attr('href');
            $('.page').removeClass('show');
            $(target_id).addClass('show');
        })
    });
    // Check for hash symbol in address
    var initial_page = '#page_setup'
    var hash = window.location.hash || initial_page;
    hash = hash.split('/')[0]; //allow for splitting has h for multiple uses
    $('a[href="'+hash+'"]').click();
    
}

SINGT.wireup.page_setup = function(){
    $("#button_measure_gain_discussion").click(function(){
        $("#measure_gain_discussion_results").html("<p>Measuring...</p>");
        // Measure gain for discussion
        command = {
            "command": "measure_gain_discussion",
        }
        json_command = JSON.stringify(command);
        console.log(json_command);
        
        // Send command
        $.ajax({
            type: "POST",
            url: "command",
            data: json_command,
            dataType: "json", // type from server
            contentType: "application/json", // type in this request
            success: function(result) {
                console.log("Server response from 'measure_gain_discussion':",result);
                $("#measure_gain_discussion_results").html(result["result"]);
            },
            error: function(first) {
                console.log("ERROR with command 'measure_gain_discussion'", first);
            }
        });
    });

    $("#button_measure_gain_recordings").click(function(){
        // Measure gain for recordings
        $("#measure_gain_recordings_results").html("<p>Measuring...</p>");
        command = {
            "command": "measure_gain_recordings",
        }
        json_command = JSON.stringify(command);
        console.log(json_command);
        
        // Send command
        $.ajax({
            type: "POST",
            url: "command",
            data: json_command,
            dataType: "json", // type from server
            contentType: "application/json", // type in this request
            success: function(result) {
                console.log("Server response from 'measure_gain_recordings':",result);
                $("#measure_gain_recordings_results").html(result["result"]);
            },
            error: function(first) {
                console.log("ERROR with command 'measure_gain_recordings'", first);
            }
        });
    });

    $("#button_measure_loop_back_latency_recordings").click(function(){
        // Measure latency
        $("#measure_loop_back_latency_recordings_results").html("<p>Measuring...</p>");
        command = {
            "command": "measure_loop_back_latency_recordings",
        }
        json_command = JSON.stringify(command);
        console.log(json_command);
        
        // Send command
        $.ajax({
            type: "POST",
            url: "command",
            data: json_command,
            dataType: "json", // type from server
            contentType: "application/json", // type in this request
            success: function(result) {
                console.log("Server response from 'measure_loop_back_latency_recordings':",result);
                $("#measure_loop_back_latency_recordings_results").html(result["result"]);
            },
            error: function(first) {
                console.log("ERROR with command 'measure_loop_back_latency_recordings'", first);
            }
        });
    });
};

SINGT.wireup.page_connect = function(){
    // Form command
    command = {
        "command": "is_connected",
    }
    json_command = JSON.stringify(command);
    console.log(json_command);
    
    // Send "is_connected" command
    $.ajax({
        type: "POST",
        url: "command",
        data: json_command,
        dataType: "json", // type from server
        contentType: "application/json", // type in this request
        success: function(result) {
            console.log("Success?");
            console.log(result);
            console.log(result["result"]);
            if (result["result"] == "success") {
                console.log("Success!");
                if (result["connected"]) {
                    $("#card_connect").addClass("d-none");
                    $("#card_connected").removeClass("d-none");
                }
                else {
                    $("#card_connect").removeClass("d-none");
                    $("#card_connected").addClass("d-none");
                }
                // Do something here
            }
        },
        error: function(first) {
            console.log("ERROR with command 'is_connected'", first);
        }
    });
};

SINGT.wireup.page_debug = function(){
    $("#button_check_playback_play").click(function(){
        // Check playback
        command = {
            "command": "debug_check_playback",
        }
        json_command = JSON.stringify(command);
        console.log(json_command);
        
        // Send command
        $.ajax({
            type: "POST",
            url: "command",
            data: json_command,
            dataType: "json", // type from server
            contentType: "application/json", // type in this request
            success: function(result) {
                console.log("Server response from 'debug_check_playback':",result);
                $("#check_playback_results").text(result["result"]);
            },
            error: function(first) {
                console.log("ERROR with command 'debug_check_playback'", first);
            }
        });
    });

    $("#button_check_playback_stop").click(function(){
        // Check playback
        command = {
            "command": "debug_stop_playback",
        }
        json_command = JSON.stringify(command);
        console.log(json_command);
        
        // Send command
        $.ajax({
            type: "POST",
            url: "command",
            data: json_command,
            dataType: "json", // type from server
            contentType: "application/json", // type in this request
            success: function(result) {
                console.log("Server response from 'debug_stop_playback':",result);
                $("#check_playback_results").text(result["result"]);
            },
            error: function(first) {
                console.log("ERROR with command 'debug_stop_playback'", first);
            }
        });
    });

    $("#button_check_recording_record").click(function(){
        // Update interface
        $("#check_recording_results").text("Recording started.");
        
        // Check playback
        command = {
            "command": "debug_record",
        }
        json_command = JSON.stringify(command);
        console.log(json_command);
        
        // Send command
        $.ajax({
            type: "POST",
            url: "command",
            data: json_command,
            dataType: "json", // type from server
            contentType: "application/json", // type in this request
            success: function(result) {
                console.log("Server response from 'debug_record':",result);
                $("#check_recording_results").text(result["result"]);
            },
            error: function(first) {
                console.log("ERROR with command 'debug_record'", first);
            }
        });
    });
};

SINGT.wireup.forms = function() {
    $("#connect-button").click(function(){
        // Get values from inputs
        username = $("#name_input").val().trim();
        address = $("#address_input").val().trim();

        // Sanity check inputs
        errors = [];
        if (username=="") {
            errors.push("Please enter a valid name.");
        }
        if (address=="") {
            errors.push("Please enter a valid IP address.");
        }

        // Alert if any errors were found
        if (errors.length != 0) {
            message = "";
            for (error of errors) {
                message += error + "\n";
            }
           
            alert(message);
            return;
        }

        // Form command
        command = {
            "command": "connect",
            "username": username,
            "address": address
        }
        json_command = JSON.stringify(command);
        console.log(json_command);

        // Send command
        $.ajax({
            type: "POST",
            url: "command",
            data: json_command,
            dataType: "json", // type from server
            contentType: "application/json", // type in this request
            success: function(result) {
                if (result["result"] == "success") {
                    $("#card_connect").addClass("d-none");
                    $("#card_connected").removeClass("d-none");
                }
                else {
                    console.log("WARNING Unexpectedly missing 'result' from host");
                    console.log(result);
                }
            },
            error: function() {
                console.log("ERROR with command 'connect'");
            }
        });

        // Stops form button from reloading page
        return false;
    })
    $("#backing_track_cancel").click(function(){
        $("#show_upload_form").parent().removeClass('d-none');
        $("#upload_form").addClass('d-none');
    })
}

$(document).ready(function(){
    SINGT.wireup();
})
