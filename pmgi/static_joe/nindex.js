var DEFAULT_IDSTR = "mp.H2O";
var infodata;

var unitPickerView;

// document.ready()
$(function(){
    config_substance();

    // ajax operation, so allow program flow to continue afterward
    async_info_request(()=>{
        config_units();
        config_modal_substance();
    });
});


function config_modal_substance(){
    $("#modal_substancepicker").load("../static/modal_substance.html", ()=>{
        sel_data_ready(infodata.data);
    });

}

function config_substance(){
    let sub = get_cookie("idstr");
    if (sub === ""){
        change_substance(DEFAULT_IDSTR);
    } else {
        display_substance(sub);
    }
}
function config_units(){
    let actual = get_cookie("units");

    // If the unit data isn't set, initialize it.
    if (actual === ""){
        change_units(infodata.units);
    } else {
        actual = JSON.parse(actual);
    }
    unitPickerView = new UnitFormView('modal_unitspicker_content',
                                            "../static/unitspicker.html",
                                            infodata.data.legalunits,
                                            actual,
                                            infodata.units,
                                            apply_units,
                                            onclick_changeunits);

    display_units(actual);
}

function apply_units(units){
    $('#modal_unitspicker').toggle();
    change_units(units)
}

function async_info_request(and_then){
    // Make an async call to get the unit data
    return ajax_info((data) =>{
        infodata = data;
        and_then();
    });
}

function onclick_changesubstance(){
    $('#modal_substancepicker').toggle();
}


function onclick_changeunits(){
    $('#modal_unitspicker').toggle();
}

function change_substance(substance){
    set_cookie("idstr", substance);
    location.reload();
}

function change_units(units){
    set_cookie("units", JSON.stringify(units));
    location.reload();
}

function display_substance(sub){
    $("#sub_string").text(sub);
}

function display_units(units){
    $("#unit_string").text(JSON.stringify(units));
}

function ajax_info(callback){
    $.get("/info",
        callback,
        'json');  // Data type of the response.
}