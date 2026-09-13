/**
 * Shared training history UI for all model nodes.
 *
 * Usage in oneditprepare:
 *   redorangeTracker.addHistoryPanel(node);
 */
(function() {
    window.redorangeTracker = window.redorangeTracker || {};

    window.redorangeTracker.addHistoryPanel = function(node) {
        $('<hr>').appendTo('#dialog-form');

        var historyBtn = $('<button type="button" class="ui-button ui-corner-all ui-widget">' +
            '<i class="fa fa-history"></i> View Training History</button>')
            .appendTo('#dialog-form');

        var container = $('<div id="or-tracker-history" style="margin-top:10px;"></div>')
            .appendTo('#dialog-form');

        historyBtn.on("click", function() {
            container.html('<div style="color:#888;">Loading training history...</div>');

            $.getJSON("redorange/tracker/runs?node_id=" + node.id, function(resp) {
                if (resp.error) {
                    container.html('<div style="color:red;">' + resp.error + '</div>');
                    return;
                }

                var runs = resp.runs || [];
                if (runs.length === 0) {
                    container.html('<div style="color:#888; font-style:italic;">No training runs recorded yet. Deploy the workflow to train a model.</div>');
                    return;
                }

                var html = '<div style="max-height:400px; overflow-y:auto;">';
                html += '<table style="width:100%; border-collapse:collapse; font-size:0.85em;">';
                html += '<thead><tr style="background:#f0f0f0;">';
                html += '<th style="padding:6px; text-align:left; border-bottom:2px solid #ccc;">Run</th>';
                html += '<th style="padding:6px; text-align:left; border-bottom:2px solid #ccc;">Time</th>';
                html += '<th style="padding:6px; text-align:left; border-bottom:2px solid #ccc;">Params</th>';
                html += '<th style="padding:6px; text-align:left; border-bottom:2px solid #ccc;">Metrics</th>';
                html += '<th style="padding:6px; text-align:center; border-bottom:2px solid #ccc;">Model</th>';
                html += '</tr></thead><tbody>';

                runs.forEach(function(run, idx) {
                    var bg = idx % 2 === 0 ? '#fff' : '#fafafa';
                    var status_icon = run.status === 'FINISHED' ? '✅' : '⏳';

                    // Format timestamp
                    var timeStr = '';
                    if (run.start_time) {
                        var d = new Date(run.start_time);
                        timeStr = d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
                    }

                    // Format params (skip data_rows/data_cols)
                    var paramParts = [];
                    for (var pk in run.params) {
                        if (pk === 'data_rows' || pk === 'data_cols') continue;
                        paramParts.push('<b>' + pk + '</b>=' + run.params[pk]);
                    }
                    var dataInfo = '';
                    if (run.params.data_rows) {
                        dataInfo = '<span style="color:#999; font-size:0.85em;">' + run.params.data_rows + '×' + run.params.data_cols + '</span>';
                    }

                    // Format metrics
                    var metricParts = [];
                    for (var mk in run.metrics) {
                        var val = run.metrics[mk];
                        var color = '#333';
                        if (mk.indexOf('CA') >= 0 || mk.indexOf('R2') >= 0) {
                            color = val >= 0.9 ? '#2d8a2d' : val >= 0.7 ? '#b8860b' : '#c33';
                        }
                        metricParts.push('<span style="color:' + color + ';"><b>' + mk + '</b>=' + val.toFixed(4) + '</span>');
                    }

                    html += '<tr style="background:' + bg + ';">';
                    html += '<td style="padding:5px; border-bottom:1px solid #eee;">' + status_icon + ' <code style="font-size:0.8em;">' + run.run_id.substring(0, 8) + '</code></td>';
                    html += '<td style="padding:5px; border-bottom:1px solid #eee; white-space:nowrap;">' + timeStr + '</td>';
                    html += '<td style="padding:5px; border-bottom:1px solid #eee;">' + paramParts.join(', ') + (dataInfo ? '<br>' + dataInfo : '') + '</td>';
                    html += '<td style="padding:5px; border-bottom:1px solid #eee;">' + metricParts.join(', ') + '</td>';
                    html += '<td style="padding:5px; border-bottom:1px solid #eee; text-align:center;">' + (run.has_model_artifact ? '💾' : '—') + '</td>';
                    html += '</tr>';
                });

                html += '</tbody></table></div>';

                // Summary bar
                var best = null;
                var bestMetric = null;
                runs.forEach(function(r) {
                    for (var mk in r.metrics) {
                        if (mk.indexOf('CA') >= 0 || mk.indexOf('R2') >= 0) {
                            if (best === null || r.metrics[mk] > bestMetric) {
                                best = r;
                                bestMetric = r.metrics[mk];
                            }
                        }
                    }
                });
                if (best) {
                    html += '<div style="margin-top:8px; padding:6px 10px; background:#e8f5e9; border-radius:4px; font-size:0.85em;">';
                    html += '🏆 <b>Best run:</b> <code>' + best.run_id.substring(0, 8) + '</code>';
                    for (var bm in best.metrics) {
                        html += ' — ' + bm + '=' + best.metrics[bm].toFixed(4);
                    }
                    html += '</div>';
                }

                html += '<div style="margin-top:6px; font-size:0.8em; color:#999;">';
                html += '<i class="fa fa-info-circle"></i> ' + runs.length + ' run(s) total. ';
                html += 'Compatible with: <code>mlflow ui --backend-store-uri ./mlruns</code>';
                html += '</div>';

                container.html(html);

            }).fail(function(jqxhr) {
                var msg = "Failed to load training history";
                try { msg = JSON.parse(jqxhr.responseText).error || msg; } catch(e) {}
                container.html('<div style="color:red;">' + msg + '</div>');
            });
        });
    };
})();
