`timescale 1ns/1ps
module matrix_adaptnet_selector #(
    parameter int MAX_M = 8,
    parameter int MAX_N = 8
)(
    input  logic                    auto_config_en,
    input  logic [15:0]             glob_m_num,
    input  logic [15:0]             glob_n_num,
    input  logic [MAX_M-1:0]        manual_row_mask,
    input  logic [MAX_N-1:0]        manual_col_mask,

    output logic [MAX_M-1:0]        selected_row_mask,
    output logic [MAX_N-1:0]        selected_col_mask,
    output logic [7:0]              selected_cfg_id,
    output logic [7:0]              active_rows,
    output logic [7:0]              active_cols
);

    localparam int HALF_M    = (MAX_M >= 2) ? (MAX_M / 2) : 1;
    localparam int HALF_N    = (MAX_N >= 2) ? (MAX_N / 2) : 1;
    localparam int QUARTER_M = (MAX_M >= 4) ? (MAX_M / 4) : 1;
    localparam int QUARTER_N = (MAX_N >= 4) ? (MAX_N / 4) : 1;

    function automatic int min_int(input int lhs, input int rhs);
        begin
            min_int = (lhs < rhs) ? lhs : rhs;
        end
    endfunction

    function automatic int abs_int(input int value);
        begin
            abs_int = (value < 0) ? -value : value;
        end
    endfunction

    function automatic int popcount_rows(input logic [MAX_M-1:0] mask);
        int idx;
        int count;
        begin
            count = 0;
            for (idx = 0; idx < MAX_M; idx++) begin
                if (mask[idx])
                    count++;
            end
            popcount_rows = count;
        end
    endfunction

    function automatic int popcount_cols(input logic [MAX_N-1:0] mask);
        int idx;
        int count;
        begin
            count = 0;
            for (idx = 0; idx < MAX_N; idx++) begin
                if (mask[idx])
                    count++;
            end
            popcount_cols = count;
        end
    endfunction

    function automatic logic [MAX_M-1:0] make_row_mask(input int active_count);
        logic [MAX_M-1:0] mask;
        int idx;
        begin
            mask = '0;
            for (idx = 0; idx < MAX_M; idx++) begin
                if (idx < active_count)
                    mask[idx] = 1'b1;
            end
            make_row_mask = mask;
        end
    endfunction

    function automatic logic [MAX_N-1:0] make_col_mask(input int active_count);
        logic [MAX_N-1:0] mask;
        int idx;
        begin
            mask = '0;
            for (idx = 0; idx < MAX_N; idx++) begin
                if (idx < active_count)
                    mask[idx] = 1'b1;
            end
            make_col_mask = mask;
        end
    endfunction

    function automatic logic [MAX_M-1:0] sanitize_row_mask(input logic [MAX_M-1:0] raw_mask);
        begin
            if (popcount_rows(raw_mask) == 0)
                sanitize_row_mask = make_row_mask(MAX_M);
            else
                sanitize_row_mask = raw_mask;
        end
    endfunction

    function automatic logic [MAX_N-1:0] sanitize_col_mask(input logic [MAX_N-1:0] raw_mask);
        begin
            if (popcount_cols(raw_mask) == 0)
                sanitize_col_mask = make_col_mask(MAX_N);
            else
                sanitize_col_mask = raw_mask;
        end
    endfunction

    function automatic int score_cfg(
        input int work_m,
        input int work_n,
        input int cfg_m,
        input int cfg_n
    );
        int active_rows_local;
        int active_cols_local;
        int active_elems;
        int idle_elems;
        int total_tiles;
        int aspect_penalty;
        begin
            active_rows_local = min_int(work_m, cfg_m);
            active_cols_local = min_int(work_n, cfg_n);
            active_elems = active_rows_local * active_cols_local;
            idle_elems = (cfg_m * cfg_n) - active_elems;
            total_tiles = ((work_m + cfg_m - 1) / cfg_m) * ((work_n + cfg_n - 1) / cfg_n);
            aspect_penalty = abs_int((work_m * cfg_n) - (work_n * cfg_m));

            score_cfg = (active_elems * 64)
                      - (idle_elems * 32)
                      - ((total_tiles - 1) * 256)
                      - aspect_penalty;
        end
    endfunction

    int work_m;
    int work_n;
    int best_score;
    int score_dense;
    int score_half_rows;
    int score_half_cols;
    int score_half_both;
    int score_quarter_rows;
    int score_quarter_cols;
    int score_quarter_both;
    int best_rows;
    int best_cols;

    logic [MAX_M-1:0] manual_row_mask_sanitized;
    logic [MAX_N-1:0] manual_col_mask_sanitized;

    always_comb begin
        manual_row_mask_sanitized = sanitize_row_mask(manual_row_mask);
        manual_col_mask_sanitized = sanitize_col_mask(manual_col_mask);

        if (!auto_config_en) begin
            selected_row_mask = manual_row_mask_sanitized;
            selected_col_mask = manual_col_mask_sanitized;
            selected_cfg_id   = 8'h80;
        end else begin
            work_m = (glob_m_num == 0) ? 1 : glob_m_num;
            work_n = (glob_n_num == 0) ? 1 : glob_n_num;

            score_dense        = score_cfg(work_m, work_n, MAX_M,     MAX_N);
            score_half_rows    = score_cfg(work_m, work_n, HALF_M,    MAX_N);
            score_half_cols    = score_cfg(work_m, work_n, MAX_M,     HALF_N);
            score_half_both    = score_cfg(work_m, work_n, HALF_M,    HALF_N);
            score_quarter_rows = score_cfg(work_m, work_n, QUARTER_M, MAX_N);
            score_quarter_cols = score_cfg(work_m, work_n, MAX_M,     QUARTER_N);
            score_quarter_both = score_cfg(work_m, work_n, QUARTER_M, QUARTER_N);

            best_score = score_dense;
            best_rows  = MAX_M;
            best_cols  = MAX_N;
            selected_cfg_id = 8'd0;

            if (score_half_rows > best_score) begin
                best_score = score_half_rows;
                best_rows  = HALF_M;
                best_cols  = MAX_N;
                selected_cfg_id = 8'd1;
            end

            if (score_half_cols > best_score) begin
                best_score = score_half_cols;
                best_rows  = MAX_M;
                best_cols  = HALF_N;
                selected_cfg_id = 8'd2;
            end

            if (score_half_both > best_score) begin
                best_score = score_half_both;
                best_rows  = HALF_M;
                best_cols  = HALF_N;
                selected_cfg_id = 8'd3;
            end

            if (score_quarter_rows > best_score) begin
                best_score = score_quarter_rows;
                best_rows  = QUARTER_M;
                best_cols  = MAX_N;
                selected_cfg_id = 8'd4;
            end

            if (score_quarter_cols > best_score) begin
                best_score = score_quarter_cols;
                best_rows  = MAX_M;
                best_cols  = QUARTER_N;
                selected_cfg_id = 8'd5;
            end

            if (score_quarter_both > best_score) begin
                best_rows  = QUARTER_M;
                best_cols  = QUARTER_N;
                selected_cfg_id = 8'd6;
            end

            selected_row_mask = make_row_mask(best_rows);
            selected_col_mask = make_col_mask(best_cols);
        end

        active_rows = popcount_rows(selected_row_mask);
        active_cols = popcount_cols(selected_col_mask);
    end

endmodule
