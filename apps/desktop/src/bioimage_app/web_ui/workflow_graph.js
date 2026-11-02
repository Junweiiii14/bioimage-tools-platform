'use strict';

// The graph is a view of the saved definition. Edits go to its owner; positions
// live in WorkflowLayout and never change computational parameters or bindings.
window.WorkflowGraph = class WorkflowGraph {
    constructor(root, onEdit, onSelect) {
        this.root = root;
        this.onEdit = onEdit;
        this.onSelect = onSelect;
        this.cards = new Map();
        this.positions = new Map();
        this.source = null;
        this.selected = '';
        this.stage = document.createElement('div');
        this.stage.className = 'wf-graph-stage';
        this.lines = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.lines.classList.add('wf-graph-lines');
        this.lines.setAttribute('aria-hidden', 'true');
        this.stage.append(this.lines);
        this.live = document.createElement('p');
        this.live.className = 'wf-graph-help';
        this.live.setAttribute('role', 'status');
        this.live.textContent =
            '选择步骤查看参数。方向键移动，Delete 删除；先选输出端口，再选输入端口连线。';
        root.append(this.live, this.stage);
        this.stage.addEventListener('click', (event) => {
            const port = event.target.closest('[data-port]');
            if (port) {
                const node = port.closest('[data-node]').dataset.node;
                if (port.dataset.direction === 'output') {
                    this.source = { node, port: port.dataset.port };
                    this.live.textContent = '已选输出，请选择要接入的输入端口。Esc 取消连线。';
                } else if (this.source) {
                    this.onEdit({
                        operation: 'connect',
                        source_node: this.source.node,
                        source_port: this.source.port,
                        target_node: node,
                        target_port: port.dataset.port,
                    });
                    this.source = null;
                    this.live.textContent = '已提交连线，请查看预检结果。';
                }
                return;
            }
            const title = event.target.closest('.wf-node-title');
            if (title) this.select(title.closest('[data-node]').dataset.node);
        });
        this.stage.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.source = null;
                this.live.textContent = '已取消连线。';
                return;
            }
            const title = event.target.closest('.wf-node-title');
            if (!title) return;
            const node = title.closest('[data-node]').dataset.node;
            if (event.key === 'Delete') {
                event.preventDefault();
                this.onEdit({ operation: 'delete_node', node_id: node });
            } else if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
                event.preventDefault();
                const p = this.positions.get(node);
                this.move(
                    node,
                    p.x + (event.key === 'ArrowLeft' ? -20 : event.key === 'ArrowRight' ? 20 : 0),
                    p.y + (event.key === 'ArrowUp' ? -20 : event.key === 'ArrowDown' ? 20 : 0),
                );
            }
        });
        this.stage.addEventListener('pointerdown', (event) => {
            const title = event.target.closest('.wf-node-title');
            if (!title || event.button !== 0) return;
            const node = title.closest('[data-node]').dataset.node;
            this.drag = {
                node,
                x: event.clientX,
                y: event.clientY,
                start: this.positions.get(node),
            };
            title.setPointerCapture(event.pointerId);
        });
        this.stage.addEventListener('pointermove', (event) => {
            if (!this.drag) return;
            const { node, x, y, start } = this.drag;
            this.positions.set(node, {
                x: start.x + event.clientX - x,
                y: start.y + event.clientY - y,
            });
            this.place(node);
            this.drawEdges();
        });
        const finishDrag = () => {
            if (!this.drag) return;
            const { node, start } = this.drag;
            const p = this.positions.get(node);
            this.drag = null;
            if (p.x !== start.x || p.y !== start.y) this.move(node, p.x, p.y);
        };
        this.stage.addEventListener('pointerup', finishDrag);
        this.stage.addEventListener('pointercancel', finishDrag);
    }
    select(node) {
        this.selected = node;
        for (const [id, card] of this.cards)
            card.querySelector('.wf-node-title').setAttribute('aria-pressed', String(id === node));
        this.onSelect(node);
    }
    move(node, x, y) {
        this.onEdit({ operation: 'move', node_id: node, x, y });
    }
    render(definition, layout, catalogue) {
        this.definition = definition;
        const ids = new Set(definition.nodes.map((node) => node.node_id));
        this.positions = new Map(
            layout.positions
                .filter((p) => ids.has(p.node_id))
                .map((p) => [p.node_id, { x: p.x, y: p.y }]),
        );
        const nodes = new Map(definition.nodes.map((node) => [node.node_id, node]));
        // Incomplete saved drafts retain unresolved edges for the owner's issue
        // list. Only edges with two declared visible endpoints have geometry.
        this.visibleEdges = definition.edges.filter(
            (edge) =>
                nodes
                    .get(edge.source_node)
                    ?.module.output_ports.some((p) => p.name === edge.source_port) &&
                nodes
                    .get(edge.target_node)
                    ?.module.input_ports.some((p) => p.name === edge.target_port),
        );
        for (const [id, card] of this.cards) {
            if (!ids.has(id)) {
                card.remove();
                this.cards.delete(id);
            }
        }
        definition.nodes.forEach((node, index) => {
            if (!this.positions.has(node.node_id))
                this.positions.set(node.node_id, { x: index * 300, y: 40 });
            const module = catalogue.find((item) => item.node_id === node.node_id);
            let card = this.cards.get(node.node_id);
            if (!card) {
                card = document.createElement('article');
                card.className = 'wf-node';
                card.dataset.node = node.node_id;
                const title = document.createElement('button');
                title.className = 'wf-node-title';
                title.type = 'button';
                card.append(title);
                this.cards.set(node.node_id, card);
                this.stage.append(card);
            }
            const title = card.querySelector('.wf-node-title');
            title.textContent = module.title;
            title.setAttribute('aria-pressed', String(node.node_id === this.selected));
            // Replacement changes a module's ports; stable cards keep keyboard focus.
            const signature = JSON.stringify([node.module, module.inputs, module.outputs]);
            if (card.dataset.module !== signature) {
                card.querySelectorAll('.wf-ports').forEach((ports) => ports.remove());
                const ports = document.createElement('div');
                ports.className = 'wf-ports';
                for (const direction of ['input', 'output']) {
                    const column = document.createElement('div');
                    column.className = 'wf-port-column';
                    for (const port of module[direction + 's']) {
                        const button = document.createElement('button');
                        button.type = 'button';
                        button.className = 'wf-port';
                        button.dataset.port = port.name;
                        button.dataset.direction = direction;
                        button.textContent = port.label;
                        button.setAttribute(
                            'aria-label',
                            module.title +
                                (direction === 'input' ? '，输入：' : '，输出：') +
                                port.label,
                        );
                        column.append(button);
                    }
                    ports.append(column);
                }
                card.append(ports);
                card.dataset.module = signature;
            }
        });
        const positions = [...this.positions.values()];
        this.origin = {
            x: Math.min(0, ...positions.map((p) => p.x)) - 40,
            y: Math.min(0, ...positions.map((p) => p.y)) - 40,
        };
        this.stage.style.width =
            Math.max(960, ...positions.map((p) => p.x - this.origin.x + 300)) + 'px';
        this.stage.style.height =
            Math.max(440, ...positions.map((p) => p.y - this.origin.y + 300)) + 'px';
        for (const id of this.cards.keys()) this.place(id);
        this.drawEdges();
    }
    place(id) {
        const p = this.positions.get(id),
            card = this.cards.get(id);
        card.style.left = p.x - this.origin.x + 'px';
        card.style.top = p.y - this.origin.y + 'px';
    }
    drawEdges() {
        this.lines.replaceChildren();
        const origin = this.stage.getBoundingClientRect();
        for (const edge of this.visibleEdges) {
            const source = this.cards
                .get(edge.source_node)
                .querySelector(
                    '[data-direction="output"][data-port="' + CSS.escape(edge.source_port) + '"]',
                )
                .getBoundingClientRect();
            const target = this.cards
                .get(edge.target_node)
                .querySelector(
                    '[data-direction="input"][data-port="' + CSS.escape(edge.target_port) + '"]',
                )
                .getBoundingClientRect();
            const x1 = source.right - origin.left,
                y1 = source.y + source.height / 2 - origin.top;
            const x2 = target.left - origin.left,
                y2 = target.y + target.height / 2 - origin.top;
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', `M${x1} ${y1} C${x1 + 60} ${y1},${x2 - 60} ${y2},${x2} ${y2}`);
            this.lines.append(path);
        }
    }
};
