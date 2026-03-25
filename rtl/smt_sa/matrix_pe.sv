module matrix_pe #(
    parameter int DATA_W      = 8,
    parameter int ACC_W       = 32,
    parameter int MAX_K       = 8,
    parameter int SMT_THREADS = 4
)(
    input  logic clk,
    input  logic rst_n,

    input  logic start,
    input  logic [$clog2(MAX_K+1)-1:0] mat_k_num,
    input  logic [MAX_K*DATA_W-1:0]    act_vec,
    input  logic [MAX_K*DATA_W-1:0]    weight_vec,

    output logic signed [ACC_W-1:0] product,
    output logic                    product_valid,
    output logic                    busy,
    output logic                    done
);

    localparam int K_W = (MAX_K <= 1) ? 1 : $clog2(MAX_K + 1);
    localparam int Q_W = (SMT_THREADS <= 1) ? 1 : $clog2(SMT_THREADS + 1);

    logic [DATA_W-1:0] q_act_r    [0:SMT_THREADS-1];
    logic [DATA_W-1:0] q_act_n    [0:SMT_THREADS-1];
    logic [DATA_W-1:0] q_weight_r [0:SMT_THREADS-1];
    logic [DATA_W-1:0] q_weight_n [0:SMT_THREADS-1];

    logic [Q_W-1:0] q_count_r, q_count_n;
    logic [K_W-1:0] scan_k_r, scan_k_n;

    logic signed [ACC_W-1:0] product_r, product_n;
    logic                    product_valid_r, product_valid_n;
    logic                    busy_r, busy_n;
    logic                    done_r, done_n;

    function automatic logic [DATA_W-1:0] get_elem(
        input logic [MAX_K*DATA_W-1:0] flat,
        input int                      elem_idx
    );
        begin
            get_elem = flat[elem_idx*DATA_W +: DATA_W];
        end
    endfunction

    integer qi;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (qi = 0; qi < SMT_THREADS; qi++) begin
                q_act_r[qi]    <= '0;
                q_weight_r[qi] <= '0;
            end
            q_count_r      <= '0;
            scan_k_r       <= '0;
            product_r      <= '0;
            product_valid_r<= 1'b0;
            busy_r         <= 1'b0;
            done_r         <= 1'b0;
        end else begin
            for (qi = 0; qi < SMT_THREADS; qi++) begin
                q_act_r[qi]    <= q_act_n[qi];
                q_weight_r[qi] <= q_weight_n[qi];
            end
            q_count_r       <= q_count_n;
            scan_k_r        <= scan_k_n;
            product_r       <= product_n;
            product_valid_r <= product_valid_n;
            busy_r          <= busy_n;
            done_r          <= done_n;
        end
    end

    integer i;
    integer lane;
    integer k_cursor;
    integer work_count_int;
    logic   stop_prefetch;
    logic [DATA_W-1:0] act_elem;
    logic [DATA_W-1:0] weight_elem;
    always_comb begin
        for (i = 0; i < SMT_THREADS; i++) begin
            q_act_n[i]    = q_act_r[i];
            q_weight_n[i] = q_weight_r[i];
        end

        q_count_n       = q_count_r;
        scan_k_n        = scan_k_r;
        product_n       = '0;
        product_valid_n = 1'b0;
        busy_n          = busy_r;
        done_n          = done_r;

        if (start) begin
            for (i = 0; i < SMT_THREADS; i++) begin
                q_act_n[i]    = '0;
                q_weight_n[i] = '0;
            end
            q_count_n       = '0;
            scan_k_n        = '0;
            product_n       = '0;
            product_valid_n = 1'b0;
            busy_n          = (mat_k_num != '0);
            done_n          = (mat_k_num == '0);
        end else if (busy_r) begin
            done_n = 1'b0;

            work_count_int = q_count_r;

            if (q_count_r != '0) begin
                product_n       = $signed(q_act_r[0]) * $signed(q_weight_r[0]);
                product_valid_n = 1'b1;
                work_count_int  = q_count_r - 1'b1;

                for (i = 0; i < SMT_THREADS-1; i++) begin
                    if (i < work_count_int) begin
                        q_act_n[i]    = q_act_r[i+1];
                        q_weight_n[i] = q_weight_r[i+1];
                    end else begin
                        q_act_n[i]    = '0;
                        q_weight_n[i] = '0;
                    end
                end

                q_act_n[SMT_THREADS-1]    = '0;
                q_weight_n[SMT_THREADS-1] = '0;
            end

            k_cursor = scan_k_r;
            stop_prefetch = 1'b0;
            for (lane = 0; lane < SMT_THREADS; lane++) begin
                if (!stop_prefetch && (k_cursor < int'(mat_k_num))) begin
                    act_elem    = get_elem(act_vec, k_cursor);
                    weight_elem = get_elem(weight_vec, k_cursor);

                    if ((act_elem == '0) || (weight_elem == '0)) begin
                        k_cursor = k_cursor + 1;
                    end else if (work_count_int < SMT_THREADS) begin
                        q_act_n[work_count_int]    = act_elem;
                        q_weight_n[work_count_int] = weight_elem;
                        work_count_int             = work_count_int + 1;
                        k_cursor                   = k_cursor + 1;
                    end else begin
                        stop_prefetch = 1'b1;
                    end
                end
            end

            q_count_n = Q_W'(work_count_int);
            scan_k_n  = K_W'(k_cursor);

            if ((k_cursor >= int'(mat_k_num)) && (work_count_int == 0)) begin
                busy_n = 1'b0;
                done_n = 1'b1;
            end else begin
                busy_n = 1'b1;
            end
        end
    end

    assign product       = product_r;
    assign product_valid = product_valid_r;
    assign busy          = busy_r;
    assign done          = done_r;

endmodule
