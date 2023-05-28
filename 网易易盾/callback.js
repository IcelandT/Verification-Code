function callback() {
    return '__JSONP_' + Math["random"]()['toString'](36)["slice"](2, 9) + '_1'
}

console.log(callback())