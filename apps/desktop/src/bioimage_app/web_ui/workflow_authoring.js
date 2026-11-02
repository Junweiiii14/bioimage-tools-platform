(() => {
    'use strict';
    const dialog = document.querySelector('#workflow-editor-dialog');
    const get = (id) => document.getElementById(id);
    const copy = (value) => structuredClone(value);
    const ports = {
        source: '原图',
        validation: '预检记录',
        analysis: '分析记录',
        measurements: '定量表',
        curves: '曲线数据',
        report: '报告',
        provenance: '运行来源',
    };
    const states = {
        running: '运行中',
        pausing: '请求暂停',
        paused: '已暂停',
        cancelling: '正在取消',
        cancelled: '已取消',
        completed: '已完成',
        completed_with_issues: '完成但有问题',
        pending: '待处理',
        succeeded: '已完成',
        issues: '待复核',
        failed: '失败',
    };
    const issueLabels = {
        draft_incomplete: '草稿尚未完整',
        missing_input: '输入尚未连接',
        scientific_role: '端口类型不匹配',
        display_into_quantitation: '显示图不能用于定量',
        unit: '单位不兼容',
        coordinate_frame: '坐标系不兼容',
        frame_origin: '原图来源不一致',
        cycle: '连接形成循环',
        parameters: '参数不符合模块要求',
        parameters_invalid: '参数未完成',
        module_admission: '模块版本当前不可用',
    };
    let bridge = null,
        saved = null,
        graph = null,
        layout = null,
        catalogue = [],
        selected = '';
    let serial = 0,
        dirty = false,
        pending = null,
        running = false,
        nativePending = false;
    let contextReady = false,
        lastStatus = null,
        outputs = [],
        refreshNeeded = false;
    let composing = false,
        parameterNode = '',
        counter = 0,
        controlPending = '';
    function element(tag, text = '', className = '') {
        const node = document.createElement(tag);
        node.textContent = text;
        node.className = className;
        return node;
    }
    function status(message, failed = false) {
        get('wf-status').textContent = message;
        get('wf-status').dataset.error = String(failed);
    }
    function markDirty() {
        serial += 1;
        dirty = true;
        bridge?.setDirty(true);
        renderChrome();
    }
    function name(id) {
        const node = graph.nodes.find((item) => item.node_id === id);
        if (!node) return '缺失步骤 ' + id;
        return (
            catalogue.find((item) => item.interface.module.module_id === node.module.module_id)
                ?.title || node.module.module_id
        );
    }
    function presentation() {
        return graph.nodes.map((node) => ({
            node_id: node.node_id,
            title: name(node.node_id),
            inputs: node.module.input_ports.map((p) => ({
                name: p.name,
                label: ports[p.name] || p.name,
            })),
            outputs: node.module.output_ports.map((p) => ({
                name: p.name,
                label: ports[p.name] || p.name,
            })),
        }));
    }
    const canvas = new WorkflowGraph(get('wf-graph'), edit, (id) => select(id));
    function renderGraph() {
        canvas.selected = selected;
        canvas.render(graph, layout, presentation());
        const list = get('wf-steps');
        list.replaceChildren();
        for (const node of graph.nodes) {
            const li = element('li'),
                button = element('button', name(node.node_id));
            button.dataset.wfSelect = node.node_id;
            button.setAttribute('aria-pressed', String(selected === node.node_id));
            li.append(button);
            list.append(li);
        }
    }
    function readParameters() {
        if (composing) {
            status('请先完成当前中文输入。');
            return false;
        }
        if (!parameterNode) return true;
        for (const field of get('wf-node-panel').querySelectorAll('[data-wf-field]')) {
            if (!field.reportValidity()) return false;
        }
        const input = get('wf-parameters');
        try {
            const value = JSON.parse(input.value);
            graph.nodes.find((node) => node.node_id === parameterNode).parameters_json =
                JSON.stringify(value);
            return true;
        } catch (error) {
            status('参数 JSON 尚未完成：' + error.message, true);
            input.focus();
            return false;
        }
    }
    function select(id) {
        if (graph && !readParameters()) return;
        selected = id;
        renderGraph();
        renderInspector();
    }
    function edit(command) {
        if (!readParameters()) return;
        if (command.operation === 'move') {
            const p = layout.positions.find((p) => p.node_id === command.node_id);
            if (p) Object.assign(p, { x: command.x, y: command.y });
            else layout.positions.push({ node_id: command.node_id, x: command.x, y: command.y });
        } else if (command.operation === 'delete_node') {
            graph.nodes = graph.nodes.filter((n) => n.node_id !== command.node_id);
            graph.edges = graph.edges.filter(
                (e) => e.source_node !== command.node_id && e.target_node !== command.node_id,
            );
            graph.inputs = graph.inputs.filter((p) => p.node_id !== command.node_id);
            graph.outputs = graph.outputs.filter((p) => p.node_id !== command.node_id);
            layout.positions = layout.positions.filter((p) => p.node_id !== command.node_id);
            selected = graph.nodes[0]?.node_id || '';
            parameterNode = '';
        } else if (command.operation === 'connect') {
            const { operation, ...edge } = command;
            graph.edges = graph.edges.filter(
                (e) => e.target_node !== edge.target_node || e.target_port !== edge.target_port,
            );
            graph.inputs = graph.inputs.filter(
                (p) => p.node_id !== edge.target_node || p.port !== edge.target_port,
            );
            graph.edges.push(edge);
        }
        markDirty();
        renderGraph();
        if (command.operation === 'delete_node') renderInspector();
        else renderLinks();
    }
    function bindRaw(node) {
        const source = saved.project.sources.find((s) => s.sample_id === graph.sample_id).asset;
        graph.inputs = graph.inputs.filter((p) => p.node_id !== node.node_id);
        for (const p of node.module.input_ports.filter((p) => p.kind === 'raw_image')) {
            graph.edges = graph.edges.filter(
                (e) => e.target_node !== node.node_id || e.target_port !== p.name,
            );
            graph.inputs.push({ node_id: node.node_id, port: p.name, asset: copy(source) });
        }
    }
    function addModule(moduleId) {
        if (!readParameters()) return;
        if (graph.nodes.length >= 64) {
            status('首版最多 64 个节点。', true);
            return;
        }
        const item = catalogue.find((c) => c.interface.module.module_id === moduleId);
        const node = {
            node_id: 'step_' + Date.now() + '_' + ++counter,
            module: copy(item.interface.module),
            parameters_json: item.parameters_json,
        };
        graph.nodes.push(node);
        bindRaw(node);
        layout.positions.push({ node_id: node.node_id, x: (graph.nodes.length - 1) * 300, y: 40 });
        selected = node.node_id;
        parameterNode = '';
        markDirty();
        renderGraph();
        renderInspector();
    }
    function renderCatalogue() {
        const root = get('wf-catalogue-list');
        root.replaceChildren();
        for (const item of catalogue) {
            const row = element('section', '', 'wf-module');
            row.append(element('strong', item.title));
            const button = element('button', '添加', 'button subtle');
            button.dataset.wfAdd = item.interface.module.module_id;
            button.setAttribute('aria-label', '添加' + item.title);
            row.append(button);
            const details = element('details');
            details.append(element('summary', '版本、端口与限制'));
            details.append(
                element(
                    'p',
                    '模块 ' +
                        item.interface.module.module_version +
                        ' · 方法 ' +
                        item.interface.module.method_version,
                ),
            );
            details.append(
                element(
                    'p',
                    item.interface.input_ports
                        .map(
                            (p) =>
                                (ports[p.name] || p.name) +
                                ': ' +
                                p.kind +
                                (p.unit ? ' / ' + p.unit : ''),
                        )
                        .join('；'),
                ),
            );
            details.append(element('p', item.limits));
            row.append(details);
            root.append(row);
        }
    }
    function renderLinks() {
        const root = get('wf-links');
        if (!root) return;
        root.replaceChildren();
        graph.edges.forEach((edge, index) => {
            const row = element(
                'p',
                name(edge.source_node) +
                    ' / ' +
                    (ports[edge.source_port] || edge.source_port) +
                    ' → ' +
                    name(edge.target_node) +
                    ' / ' +
                    (ports[edge.target_port] || edge.target_port),
            );
            const remove = element('button', '移除这条连接', 'text-button');
            remove.dataset.wfDisconnect = String(index);
            row.append(remove);
            root.append(row);
        });
    }
    function renderInspector() {
        const root = get('wf-node-panel');
        root.replaceChildren();
        parameterNode = '';
        const node = graph.nodes.find((node) => node.node_id === selected);
        if (!node) {
            root.append(element('h3', '从目录添加或选择一个步骤'));
            return;
        }
        root.append(element('h3', name(node.node_id)));
        const version = element(
            'p',
            '模块 ' + node.module.module_version + ' · 方法 ' + node.module.method_version,
        );
        root.append(version);
        const replacement = element('select');
        replacement.id = 'wf-replacement';
        for (const item of catalogue) {
            const option = element('option', item.title);
            option.value = item.interface.module.module_id;
            replacement.append(option);
        }
        replacement.value = node.module.module_id;
        root.append(replacement);
        const replace = element('button', '用目录模块替换此步骤', 'button subtle');
        replace.id = 'wf-replace';
        root.append(replace);
        const json = element('textarea');
        json.id = 'wf-parameters';
        json.setAttribute('aria-label', '步骤完整参数');
        json.value = JSON.stringify(JSON.parse(node.parameters_json), null, 2);
        parameterNode = node.node_id;
        const item = catalogue.find((c) => c.interface.module.module_id === node.module.module_id);
        if (item) {
            const schema = JSON.parse(item.interface.module.parameters_schema);
            const labels = {
                polarity: '信号极性',
                layout: '报告布局',
                quant_policy: '定量策略',
                geometry_policy: '几何策略',
                lanes: '泳道',
                roi: '原图 ROI（像素）',
                bands: '条带',
                bounds: '积分区间（ROI 内行坐标，含左右端点）',
                left: '左端点',
                right: '右端点',
                baseline: '基线',
                lane_id: '泳道标识',
                band_id: '条带标识',
                expected_rows: '预期条带数',
                x0: 'X 起点',
                x1: 'X 终点（不含）',
                y0: 'Y 起点',
                y1: 'Y 终点（不含）',
                revision: '方法输入修订',
                schema_version: '参数版本',
            };
            function fieldSchema(field) {
                if (field.$ref) return schema.$defs[field.$ref.split('/').pop()];
                if (field.anyOf) return fieldSchema(field.anyOf.find((f) => f.type !== 'null'));
                return field;
            }
            function update(path, value) {
                const params = JSON.parse(json.value);
                let parent = params;
                for (const key of path.slice(0, -1)) parent = parent[key];
                parent[path.at(-1)] = value;
                node.parameters_json = JSON.stringify(params);
                json.value = JSON.stringify(params, null, 2);
                markDirty();
            }
            function field(parent, key, value, declaration, path) {
                const spec = fieldSchema(declaration),
                    title = labels[key] || key;
                if (value !== null && typeof value === 'object') {
                    const group = element('fieldset', '', 'wf-param-group');
                    group.append(element('legend', title));
                    if (Array.isArray(value)) {
                        value.forEach((entry, index) => {
                            const row = element('div', '', 'wf-param-entry');
                            field(
                                row,
                                String(index + 1),
                                entry,
                                spec.prefixItems?.[index] || spec.items || {},
                                [...path, index],
                            );
                            const remove = element('button', '删除此项', 'button subtle');
                            remove.addEventListener('click', () => {
                                if (!readParameters()) return;
                                let current = JSON.parse(node.parameters_json);
                                for (const key of path) current = current[key];
                                update(
                                    path,
                                    current.filter((_, i) => i !== index),
                                );
                                renderInspector();
                            });
                            if (!spec.prefixItems) row.append(remove);
                            group.append(row);
                        });
                        if (value.length && !spec.prefixItems) {
                            const add = element(
                                'button',
                                '复制末项（请修改标识与坐标）',
                                'button subtle',
                            );
                            add.addEventListener('click', () => {
                                if (!readParameters()) return;
                                // The copied values remain explicit drafts; host preflight checks identity.
                                const params = JSON.parse(node.parameters_json);
                                let current = params;
                                for (const key of path) current = current[key];
                                update(path, [...current, copy(current.at(-1))]);
                                renderInspector();
                            });
                            group.append(add);
                        }
                    } else {
                        for (const [child, entry] of Object.entries(value))
                            field(group, child, entry, spec.properties?.[child] || {}, [
                                ...path,
                                child,
                            ]);
                    }
                    parent.append(group);
                    return;
                }
                if (value === null) {
                    parent.append(element('p', title + '：未设置；可在高级参数中明确填写。'));
                    return;
                }
                const label = element('label', title),
                    input = element(spec.enum ? 'select' : 'input');
                input.dataset.wfField = path.join('.');
                input.dataset.wfParam = path.join('.');
                if (spec.enum) {
                    for (const choice of spec.enum) {
                        const option = element('option', choice);
                        option.value = choice;
                        input.append(option);
                    }
                } else {
                    input.type =
                        typeof value === 'number'
                            ? 'number'
                            : typeof value === 'boolean'
                              ? 'checkbox'
                              : 'text';
                    input.required = true;
                    if (input.type === 'number') input.step = spec.type === 'integer' ? '1' : 'any';
                }
                input.value = String(value);
                if (typeof value === 'boolean') input.checked = value;
                input.disabled = spec.const !== undefined;
                input.addEventListener(spec.enum ? 'change' : 'input', () => {
                    if (!input.validity.valid) {
                        markDirty();
                        return;
                    }
                    if (!readParameters()) return;
                    update(
                        path,
                        typeof value === 'number'
                            ? input.valueAsNumber
                            : typeof value === 'boolean'
                              ? input.checked
                              : input.value,
                    );
                });
                input.addEventListener('compositionstart', () => {
                    composing = true;
                });
                input.addEventListener('compositionend', () => {
                    composing = false;
                });
                label.append(input);
                parent.append(label);
            }
            const params = JSON.parse(node.parameters_json);
            for (const [key, value] of Object.entries(params))
                field(root, key, value, schema.properties[key] || {}, [key]);
        }
        const advanced = element('details');
        advanced.append(element('summary', '高级：完整参数 JSON'));
        const label = element('label', '原图像素坐标；编辑后保存并预检');
        label.append(json);
        advanced.append(label);
        root.append(advanced);
        json.addEventListener('input', markDirty);
        json.addEventListener('compositionstart', () => {
            composing = true;
            markDirty();
        });
        json.addEventListener('compositionend', () => {
            composing = false;
        });
        for (const [id, text] of [
            ['wf-bind-raw', '将原图绑定到本步骤'],
            ['wf-mark-output', '切换本步骤为流程成果'],
            ['wf-node-results', '查看本步骤已提交成果'],
            ['wf-delete-node', '删除本步骤'],
        ]) {
            const button = element('button', text, 'button subtle');
            button.id = id;
            root.append(button);
        }
        const details = element('details');
        details.append(element('summary', '全部连接与参数 schema'));
        const links = element('div', '', 'wf-links');
        links.id = 'wf-links';
        details.append(links);
        const pre = element(
            'pre',
            JSON.stringify(JSON.parse(node.module.parameters_schema), null, 2),
        );
        details.append(pre);
        root.append(details);
        renderLinks();
    }
    function renderChecks() {
        const root = get('wf-issues');
        root.replaceChildren();
        for (const issue of saved?.issues || [])
            root.append(
                element(
                    'li',
                    (issue.node_id ? name(issue.node_id) + '：' : '') +
                        (issueLabels[issue.code] || '预检未通过') +
                        ' · ' +
                        issue.message,
                ),
            );
        get('wf-check-summary').textContent = dirty
            ? '当前修改尚未预检；保存会保留草稿并检查连接与参数。'
            : saved?.issues.length
              ? '草稿已保存，运行仍被预检问题阻止。'
              : '最近保存的流程通过预检。';
        get('wf-sources').textContent = (saved?.project.sources || [])
            .map((s) => s.label + (s.reason ? '：' + s.reason : ' · 原图已保留'))
            .join('；');
    }
    function renderResults() {
        const root = get('wf-output-list');
        root.replaceChildren();
        const summary = get('wf-sample-states');
        summary.replaceChildren();
        for (const sample of saved?.samples || []) {
            const row = element(
                'p',
                sample.label +
                    ' · ' +
                    (states[sample.state] || sample.state) +
                    (sample.reason ? '：' + sample.reason : ''),
                'wf-sample',
            );
            row.dataset.state = sample.state;
            summary.append(row);
        }
        if (!outputs.length)
            root.append(element('p', '尚无已提交的成果。未完成、失败与零值分开显示。'));
        outputs.forEach((output, index) => {
            const section = element('section', '', 'wf-result-item');
            section.append(element('h3', ports[output.port] || output.port));
            if (output.table.length) {
                const wrap = element('div', '', 'wf-table-wrap'),
                    table = element('table');
                wrap.tabIndex = 0;
                output.table.forEach((row, r) => {
                    const tr = element('tr');
                    row.forEach((cell) =>
                        tr.append(element(r ? 'td' : 'th', cell === '' ? '—' : cell)),
                    );
                    table.append(tr);
                });
                wrap.append(table);
                section.append(wrap);
                section.append(
                    element(
                        'p',
                        '预览前 ' +
                            Math.min(100, output.table_rows) +
                            ' 行 / 共 ' +
                            output.table_rows +
                            ' 行。空值为 —，有效零保留原值。',
                    ),
                );
            }
            if (output.preview) {
                const image = element('img');
                image.src = output.preview;
                image.alt = '从已提交资产读取的报告';
                section.append(image);
            }
            const button = element('button', '打开已核验文件', 'button subtle');
            button.dataset.wfOpenOutput = String(index);
            section.append(button);
            const details = element('details');
            details.append(element('summary', '运行与来源'));
            details.append(
                element(
                    'p',
                    '批次 ' +
                        output.batch_id +
                        ' · 样本 ' +
                        output.sample_id +
                        ' · 资产 SHA256 ' +
                        output.asset.sha256,
                ),
            );
            section.append(details);
            root.append(section);
        });
    }
    function renderChrome() {
        get('wf-start').hidden = contextReady;
        get('wf-workspace').hidden = !contextReady;
        get('wf-title').disabled = !contextReady;
        get('wf-save').disabled = !contextReady || !!pending;
        get('wf-run').disabled = !contextReady || !!pending || running;
        get('wf-revert').disabled = !dirty || !!pending;
        get('wf-pause').hidden = !running || lastStatus?.state !== 'running';
        get('wf-resume').hidden =
            !running ||
            !(lastStatus?.state === 'paused' || lastStatus?.phase === 'awaiting_resume');
        get('wf-cancel').hidden = !running && pending?.operation !== 'freeze';
        get('wf-pause').disabled = !!controlPending;
        get('wf-resume').disabled = !!controlPending;
        get('wf-save-state').textContent = saved
            ? '已保存修订 ' + saved.project.revision + (dirty ? ' · 还有未保存编辑' : '')
            : '';
        document.querySelectorAll('[data-workflow-open]').forEach((b) => {
            b.textContent = running
                ? '工作流 · ' + (states[lastStatus?.state] || '处理中')
                : '工作流编排';
        });
        if (saved) renderChecks();
    }
    function send(operation, values = {}, chooseAction = '') {
        if (!bridge) {
            status('此操作需要桌面工作台。', true);
            return;
        }
        if (pending) return;
        const token = 'wf-' + Date.now() + '-' + ++counter;
        pending = {
            token,
            operation,
            serial,
            context: ['new_original', 'new_template', 'new_example', 'open_project'].includes(
                chooseAction,
            ),
            wasReady: contextReady,
        };
        status('正在' + (operation === 'freeze' ? '保存并预检运行请求…' : '处理…'));
        renderChrome();
        if (chooseAction) bridge.choose(token, chooseAction, JSON.stringify(values));
        else
            bridge.command(
                token,
                JSON.stringify({ operation, document_id: saved.project.document_id, ...values }),
            );
    }
    function choose(action) {
        if (!readParameters()) return;
        if (action === 'new_original' && !get('wf-lane-count').value) {
            status('请填写已知泳道数。', true);
            get('wf-lane-count').focus();
            return;
        }
        send(
            action,
            {
                validation: action === 'bind_example' ? 'triangle_u8' : get('wf-example').value,
                lane_count: Number(get('wf-lane-count').value),
                polarity: get('wf-polarity').value,
            },
            action,
        );
        dialog.querySelectorAll('.wf-menu[open]').forEach((menu) => {
            menu.open = false;
        });
    }
    function save(run) {
        if (!readParameters()) return;
        send(run ? 'freeze' : 'save', { previous_revision: saved.project.revision, graph, layout });
    }
    function received(token, operation, data, error) {
        const request = pending?.token === token ? pending : null;
        if (request) pending = null;
        if (error) {
            controlPending = '';
            if (request?.context) contextReady = false;
            status(error, true);
            renderChrome();
            return;
        }
        if (operation === 'cancelled') {
            if (request) contextReady = request.wasReady;
            status('已取消文件选择。');
            renderChrome();
            return;
        }
        let incoming;
        try {
            incoming = JSON.parse(data);
        } catch (failure) {
            status('工作流回执无法读取，当前草稿保留。', true);
            return;
        }
        const replace =
            !graph || request?.context || operation === 'initialize' || operation === 'bind';
        saved = incoming;
        catalogue = incoming.catalogue;
        if (replace) {
            graph = copy(incoming.project.graph);
            layout = copy(incoming.project.layout);
            serial = 0;
            dirty = false;
            contextReady = true;
            selected = graph.nodes.some((node) => node.node_id === selected)
                ? selected
                : graph.nodes[0]?.node_id || '';
            parameterNode = '';
            outputs = [];
            get('wf-title').value = graph.title;
            renderCatalogue();
            renderGraph();
            renderInspector();
            renderResults();
        } else if (operation === 'save' || operation === 'freeze') {
            graph.revision = incoming.project.graph.revision;
            dirty = !request || serial !== request.serial;
        }
        bridge.setDirty(dirty);
        if (operation === 'results' || operation === 'open') {
            outputs = incoming.outputs;
            renderResults();
        }
        status(
            incoming.issues.length
                ? '草稿已保存，仍有预检问题；未派发新的计算。'
                : dirty
                  ? '提交时的修订已保存，你后续编辑仍保留。'
                  : operation === 'freeze'
                    ? '已保存并冻结运行计划，执行状态以真实回执为准。'
                    : '已读取或保存工作流。',
        );
        renderChrome();
        if (refreshNeeded && !pending && contextReady) {
            refreshNeeded = false;
            send('results');
        }
    }
    function view(value) {
        dialog.dataset.view = value;
        dialog
            .querySelectorAll('[data-wf-view]')
            .forEach((button) =>
                button.setAttribute('aria-pressed', String(button.dataset.wfView === value)),
            );
    }
    dialog.addEventListener('click', (event) => {
        const button = event.target.closest('button');
        if (!button) return;
        if (button.dataset.wfChoose) {
            choose(button.dataset.wfChoose);
            return;
        }
        if (button.dataset.wfView) {
            view(button.dataset.wfView);
            if (button.dataset.wfView === 'results' && saved?.project.last_batch_id)
                send('results');
            return;
        }
        if (button.dataset.wfAdd) {
            addModule(button.dataset.wfAdd);
            return;
        }
        if (button.dataset.wfSelect) {
            select(button.dataset.wfSelect);
            return;
        }
        if (button.dataset.wfDisconnect !== undefined) {
            if (!readParameters()) return;
            graph.edges.splice(Number(button.dataset.wfDisconnect), 1);
            markDirty();
            renderGraph();
            renderLinks();
            return;
        }
        if (button.dataset.wfOpenOutput !== undefined) {
            const output = outputs[Number(button.dataset.wfOpenOutput)];
            send('open', {
                batch_id: output.batch_id,
                sample_id: output.sample_id,
                node_id: output.node_id,
                port: output.port,
            });
            return;
        }
        const node = graph?.nodes.find((node) => node.node_id === selected);
        if (button.id === 'wf-hide') dialog.close();
        else if (button.id === 'wf-save') save(false);
        else if (button.id === 'wf-run') save(true);
        else if (['wf-pause', 'wf-resume', 'wf-cancel'].includes(button.id)) {
            controlPending = button.id.slice(3);
            bridge.control(controlPending);
            status(
                '已请求' +
                    { pause: '暂停', resume: '继续', cancel: '取消' }[controlPending] +
                    '，等待实际回执。',
            );
            renderChrome();
        } else if (button.id === 'wf-revert') {
            graph = copy(saved.project.graph);
            layout = copy(saved.project.layout);
            serial += 1;
            dirty = false;
            parameterNode = '';
            bridge.setDirty(false);
            get('wf-title').value = graph.title;
            renderGraph();
            renderInspector();
            renderChrome();
        } else if (button.id === 'wf-delete-node')
            edit({ operation: 'delete_node', node_id: selected });
        else if (button.id === 'wf-bind-raw') {
            if (!readParameters()) return;
            bindRaw(node);
            markDirty();
            renderGraph();
            renderLinks();
        } else if (button.id === 'wf-mark-output') {
            if (!readParameters()) return;
            const marked = graph.outputs.some((p) => p.node_id === selected);
            graph.outputs = graph.outputs.filter((p) => p.node_id !== selected);
            if (!marked)
                for (const port of node.module.output_ports)
                    graph.outputs.push({
                        name: node.node_id + '_' + port.name,
                        node_id: selected,
                        port: port.name,
                    });
            markDirty();
            renderChrome();
        } else if (button.id === 'wf-replace') {
            if (!readParameters()) return;
            const item = catalogue.find(
                (c) => c.interface.module.module_id === get('wf-replacement').value,
            );
            node.module = copy(item.interface.module);
            node.parameters_json = item.parameters_json;
            graph.edges = graph.edges.filter(
                (e) =>
                    (e.source_node !== selected ||
                        node.module.output_ports.some((p) => p.name === e.source_port)) &&
                    (e.target_node !== selected ||
                        node.module.input_ports.some((p) => p.name === e.target_port)),
            );
            graph.outputs = graph.outputs.filter(
                (p) =>
                    p.node_id !== selected ||
                    node.module.output_ports.some((port) => port.name === p.port),
            );
            bindRaw(node);
            parameterNode = '';
            markDirty();
            renderGraph();
            renderInspector();
        } else if (button.id === 'wf-node-results') {
            if (saved.project.last_batch_id) {
                view('results');
                send('results', { node_id: selected });
            }
        } else if (button.id === 'wf-refresh-results') send('results');
    });
    get('wf-title').addEventListener('input', () => {
        graph.title = get('wf-title').value;
        markDirty();
    });
    dialog.addEventListener('cancel', (event) => {
        event.preventDefault();
        dialog.close();
    });
    dialog.addEventListener('keydown', (event) => {
        if (
            !event.isComposing &&
            (event.ctrlKey || event.metaKey) &&
            event.key.toLowerCase() === 's'
        ) {
            event.preventDefault();
            event.stopPropagation();
            if (contextReady && !pending) save(false);
        }
    });
    document.querySelectorAll('[data-workflow-open]').forEach((button) =>
        button.addEventListener('click', () => {
            if (!dialog.open) dialog.showModal();
        }),
    );
    window.workflowEditor = {
        connect(value) {
            bridge = value;
            bridge.documentChanged.connect(received);
            bridge.workspaceChanged.connect((path) => {
                get('wf-workspace-path').textContent = path;
            });
            bridge.activityChanged.connect((p, r) => {
                nativePending = p;
                running = r;
                renderChrome();
            });
            bridge.progressChanged.connect((raw) => {
                const next = JSON.parse(raw);
                lastStatus = next;
                if (next.state !== 'running' || controlPending === 'resume') controlPending = '';
                const step = saved?.execution_nodes.find((n) => n.node_id === next.child?.node_id);
                status(
                    (states[next.state] || next.state) +
                        ' · 完成 ' +
                        (next.succeeded + next.issues) +
                        '/' +
                        next.total +
                        ' · 失败 ' +
                        next.failed +
                        (step ? ' · ' + step.title : '') +
                        (dirty || !saved?.matches_run ? '（已冻结批次，当前草稿单独保留）' : '') +
                        (next.message ? ' · ' + next.message : ''),
                    !!next.message,
                );
                if (next.phase === 'closed') {
                    if (pending) refreshNeeded = true;
                    else if (contextReady) send('results');
                }
                renderChrome();
            });
            bridge.revealRequested.connect(() => {
                if (!dialog.open) dialog.showModal();
            });
            bridge.draftDiscarded.connect(() => {
                if (saved) {
                    graph = copy(saved.project.graph);
                    layout = copy(saved.project.layout);
                    dirty = false;
                    serial += 1;
                    parameterNode = '';
                    renderGraph();
                    renderInspector();
                    renderChrome();
                }
            });
            renderChrome();
        },
        hasDraft: () => dirty,
        snapshot: () => ({
            selected,
            dirty,
            serial,
            pending: pending?.operation,
            nativePending,
            running,
            graph: copy(graph),
            layout: copy(layout),
        }),
    };
})();
