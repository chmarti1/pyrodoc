
//**************
// Cookie management functions
//**************

// Set a cookie value
//      set_cookie(param,value)
// This assigns a value to the string parameter name, param.  The cookie
// expiration is not set.
function set_cookie(param, value){
    // Set the cookie to expire in one hour
    set_cookie_exp(param,value,3600000);
}

// Set a cookie with an expiration value
//      set_cookie_exp(param,value,exp)
// This assigns a value to the string parameter name, param.  The cookie
// expiration is set to exp milliseconds from now.  To delete a cookie,
// pass a negative value to exp
function set_cookie_exp(param, value, exp){
    // Set the cookie to expire in one hour
    time = new Date();
    time.setTime(time.getTime() + exp);
    document.cookie= param + '=' + value + ';expires=' + time + ';path=/'+';SameSite=Lax';
}

// GET_COOKIE
//      get_cookie(param)
// Recovers the value associated with a cookie with the string name,
// param.  If no cookie with a matching param name is found, an empty
// string is returned.
function get_cookie(param){
    let pairs = decodeURIComponent(document.cookie).split(';');
    let tparam, declare, value;
    // Loop over the parameter-value pairs
    for(declare of pairs){
        // Split by =
        pair = declare.split('=')
        if(pair.length == 2){
            tparam = pair[0].trim();
            value = pair[1].trim();
            if(tparam==param){
                return value;
            }
        }
    }
    return '';
}
