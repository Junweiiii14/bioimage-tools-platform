"""Presentation of committed original-pixel measurements, never browser-side analysis."""

from wb_tool.api import WBAnalysisProject, analysis_is_current, ordered_quant_rows

from bioimage_app.figure_window import FigureProjectWindow


def quant_snapshot(host: FigureProjectWindow) -> dict[str, object]:
    project = host.view.project()
    selected = host.view.selected_row()
    plans = project.analyses if isinstance(project, WBAnalysisProject) else ()
    table: list[dict[str, object]] = []
    selected_lanes: list[dict[str, object]] = []
    group_rows: list[dict[str, object]] = []
    order_by_figure = {figure: i for i, figure in enumerate(project.figure_order, 1)}
    ordered = [(order_by_figure[row.figure], row) for row in ordered_quant_rows(project)]
    for order, row in ordered:
        plan = next((p for p in plans if p.row_id == row.row_id), None)
        current = bool(plan and analysis_is_current(project, plan))
        loaded = next(
            (
                r
                for r in host.project_results
                if plan
                and current
                and plan.run
                and r.run_id == plan.run.run_id
                and r.row_id == row.row_id
                and r.result.request == plan.request
            ),
            None,
        )
        band_rows: dict[int, list[dict[str, object]]] = {}
        row_lanes: list[dict[str, object]] = []
        if plan and current:
            for index, annotation in enumerate(plan.request.lanes, 1):
                result = (
                    next((r for r in loaded.result.lanes if r.roi == annotation.roi), None)
                    if loaded
                    else None
                )
                bands: list[dict[str, object]] = []
                included_index = 0
                for band in annotation.bands:
                    measured = (
                        next(
                            (b for b in result.bands if b.annotation.band_id == band.band_id), None
                        )
                        if result
                        else None
                    )
                    actual = measured.annotation if measured else band
                    measurement = measured.measurement if measured else None
                    baseline = measurement.baseline if measurement else actual.baseline
                    bounds = measurement.bounds if measurement else actual.bounds
                    status = measured.status if measured else "not_run"
                    reason = measured.reason if measured else "等待当前参数计算"
                    notes = actual.detection_notes
                    reason = "；".join(dict.fromkeys(v for v in (reason, *notes) if v))
                    signal = measurement.signal if measurement else None
                    bands.append(
                        {
                            "id": actual.band_id,
                            "label": (row.protein or "条带") + " · " + actual.band_id,
                            "start": bounds.left if bounds else None,
                            "end": bounds.right if bounds else None,
                            "baselineStart": baseline.left_value if baseline else None,
                            "baselineEnd": baseline.right_value if baseline else None,
                            "signal": signal,
                            "status": status,
                            "reason": reason or "",
                        }
                    )
                    if actual.included:
                        included_index += 1
                        band_rows.setdefault(included_index, []).append(
                            {
                                "lane": index,
                                "bandId": actual.band_id,
                                "signal": signal,
                                "status": status,
                                "reason": reason or "",
                            }
                        )
                if selected and row.figure == selected.figure:
                    roi = annotation.roi
                    row_lanes.append(
                        {
                            "lane": index,
                            "laneId": roi.lane_id,
                            "roi": {
                                "x": roi.x0,
                                "y": roi.y0,
                                "width": roi.width,
                                "height": roi.y1 - roi.y0,
                            },
                            "profile": list(result.profiles.quantitative)
                            if result and result.profiles
                            else [],
                            "bands": bands,
                        }
                    )
        else:
            band_rows[1] = [
                {
                    "lane": i,
                    "signal": None,
                    "status": "unconfigured",
                    "reason": "请自动规划当前原图泳道",
                }
                for i in range(1, row.lane_count + 1)
            ]
        if selected and row.figure == selected.figure:
            group_rows.append({"rowId": row.row_id, "protein": row.protein, "lanes": row_lanes})
            if row.row_id == selected.row_id:
                selected_lanes = row_lanes
        if not band_rows:
            band_rows[1] = []
        for number, values in sorted(band_rows.items()):
            table.append(
                {
                    "rowId": row.row_id,
                    "groupOrder": f"第 {order} 组",
                    "groupName": row.figure or f"第 {order} 组",
                    "band": "target" if number == 1 else f"target-{number}",
                    "label": row.protein if len(band_rows) == 1 else f"{row.protein} · {number}",
                    "values": values,
                }
            )
    members = [r for r in project.rows if selected and r.figure == selected.figure]
    present = [r for r in members if r.source]
    compatible = (
        bool(present) and len({r.lane_count for r in present}) == 1 and all(r.roi for r in present)
    )
    return {
        "rowOrder": [row.row_id for _, row in ordered],
        "group": {
            "figure": selected.figure if selected else "",
            "rows": group_rows,
            "laneCount": present[0].lane_count if compatible else 0,
            "compatible": compatible,
            "reason": "" if compatible else "组内各蛋白行须有裁剪且泳道数一致，才能按列对应定量",
        },
        "rowId": selected.row_id if selected else "",
        "sourceId": selected.source.sha256 if selected and selected.source else "",
        "revision": host.view.generation,
        "status": "busy"
        if host.operation_busy
        else "ready"
        if selected_lanes and all(lane["profile"] for lane in selected_lanes)
        else "pending"
        if selected_lanes
        else "unconfigured",
        "reason": "原图曲线扣除直线封底后的积分；质量提示与数值分别保留。",
        "lanes": selected_lanes,
        "table": table,
    }
