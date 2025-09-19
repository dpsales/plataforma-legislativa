//  assets/dashAgGridComponentFunctions.js
var dagcomponentfuncs = window.dashAgGridComponentFunctions =
    window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.markdownLinkRenderer = function (props) {
    const md = props.value || '';
    const m = md.match(/\[([^\]]+)\]\(([^)]+)\)/);
    if (m) {
        return React.createElement(
            'a',
            {
                href: m[2],
                target: '_blank',
                rel: 'noopener noreferrer'
            },
            m[1]
        );
    }
    return md;
};
