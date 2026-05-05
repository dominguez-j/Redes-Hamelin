local rftp = Proto("RFTP", "Protocolo de transferencia de archivos confiable")

local rftp_checksum         = ProtoField.uint16("rftp.checksum", "Checksum", base.HEX)
local rftp_sequenceNumber   = ProtoField.uint16("rftp.seq", "Número de secuencia", base.DEC)
local rftp_payloadLength    = ProtoField.uint16("rftp.plength", "Longitud de payload", base.DEC, nil, 0xffe0)
local rftp_flags            = ProtoField.uint16("rftp.flags", "Flags", base.BIN, nil, 0x003f)
local rftp_payload          = ProtoField.bytes("rftp.payload", "Payload")

local rftp_flag_syn     = ProtoField.bool("rftp.flags.syn", "SYN", 16, nil, 0x0020)
local rftp_flag_ack     = ProtoField.bool("rftp.flags.ack", "ACK", 16, nil, 0x0010)
local rftp_flag_err     = ProtoField.bool("rftp.flags.err", "ERR", 16, nil, 0x0008)
local rftp_flag_ctype   = ProtoField.bool("rftp.flags.ctype", "CTYP", 16, nil, 0x0004)
local rftp_flag_ptype   = ProtoField.bool("rftp.flags.ptype", "PTYP", 16, nil, 0x0002)
local rftp_flag_fin     = ProtoField.bool("rftp.flags.fin", "FIN", 16, nil, 0x0001)

-- Sacado de SYN
local rftp_payload_filename = ProtoField.string("rftp.filename", "Nombre del archivo")

-- Caso de ERR
local rftp_err_desc = ProtoField.string("rftp.err.description", "Error")

-- Caso de SYN + Carga
local rftp_payload_file_size = ProtoField.uint32("rftp.upload.filesize", "Tamaño del archivo (Bytes)")

-- Caso de PTYPE
local rftp_ptype_name = ProtoField.string("rftp.ptype.name", "Tipo de protocolo")

-- Caso de CTYPE
local rftp_ctype_name = ProtoField.string("rftp.ctype.name", "Tipo de cliente")

rftp.fields = {
    rftp_checksum,
    rftp_sequenceNumber,
    rftp_payloadLength,
    rftp_flags,
    rftp_flag_syn,
    rftp_flag_ack,
    rftp_flag_err,
    rftp_flag_ctype,
    rftp_flag_ptype,
    rftp_flag_fin,
    rftp_payload,

    -- Sacado de SYN
    rftp_payload_filename,

    -- Sacado de ERR
    rftp_err_desc,

    -- Caso de SYN + Carga
    rftp_payload_file_size,

    -- Caso de PTYPE
    rftp_ptype_name,

    -- Caso de PTYPE
    rftp_ctype_name,
}

function rftp.dissector(buffer, pinfo, tree)
    if buffer:len() < 8 then return end

    pinfo.cols.protocol = "RFTP"

    local subtree = tree:add(rftp, buffer(), "RFTP")

    subtree:add(rftp_checksum,       buffer(0, 2))
    subtree:add(rftp_sequenceNumber, buffer(2, 2))

    subtree:add(rftp_payloadLength,  buffer(4, 2))

    local flags_tree = subtree:add(rftp_flags, buffer(6, 2))
    flags_tree:add(rftp_flag_syn,   buffer(6, 2))
    flags_tree:add(rftp_flag_ack,   buffer(6, 2))
    flags_tree:add(rftp_flag_err,   buffer(6, 2))
    flags_tree:add(rftp_flag_ctype, buffer(6, 2))
    flags_tree:add(rftp_flag_ptype, buffer(6, 2))
    flags_tree:add(rftp_flag_fin,   buffer(6, 2))

    local payload_len = buffer(4, 2):uint()
    payload_len = bit.rshift(bit.band(payload_len, 0xFFE0), 5)
    -- if payload_len > 0 and buffer:len() >= 8 + payload_len then
    --     subtree:add(rftp_payload, buffer(8, payload_len))
    -- end

    local seq   = buffer(2, 2):uint()
    local flags = bit.band(buffer(6, 2):uint(), 0x003F)
    local syn   = bit.band(flags, 0x0020) ~= 0
    local ack   = bit.band(flags, 0x0010) ~= 0
    local ctyp  = bit.band(flags, 0x0004) ~= 0
    local ptyp  = bit.band(flags, 0x0002) ~= 0
    local fin   = bit.band(flags, 0x0001) ~= 0
    local err   = bit.band(flags, 0x0008) ~= 0
    local flag_str = (syn and "SYN " or "") ..
                     (ack and "ACK " or "") ..
                     (fin and "FIN " or "") ..
                     (err and "ERR " or "")

    -- Según los flags

    -- File name
    if syn and not ack and payload_len > 0 and buffer:len() >= 8 + payload_len then
        if ctyp then
            local filename_start = 8
            if buffer(8, 4):uint() == 0 then
                filename_start = 12
            end

            local name_len = payload_len - (filename_start - 8)
            if name_len > 0 then
                subtree:add(rftp_payload_filename, buffer(filename_start, name_len))
            end
        else
            -- Carga: 4 bytes filesize + nombre
            subtree:add(rftp_payload_file_size, buffer(8, 4))
            if payload_len > 4 then
                subtree:add(rftp_payload_filename, buffer(12, payload_len - 4))
            end
        end
    end

    if err and payload_len > 0 then
        subtree:add(rftp_err_desc, buffer(8, payload_len))
    end


    -- Client type
    local ctype_item = subtree:add(rftp_ctype_name, "")
    ctype_item:set_text(ctyp and "Cliente: Descarga" or "Cliente: Carga")

    -- Protocol type
    local ptype_item = subtree:add(rftp_ptype_name, "")
    ptype_item:set_text(ptyp and "Protocolo: Selective Repeat" or "Protocolo: Stop & Wait")

    pinfo.cols.info = string.format("Seq=%d  Len=%d  [%s]", seq, payload_len, flag_str)

    return buffer:len()
end

local function dissect_rftp_heur(buffer, pinfo, tree)
    -- Validación mínima para evitar falsos positivos
    -- Por ejemplo: longitud mínima de 8 bytes
    if buffer:len() < 8 then return false end

    -- Si pasa la validación, llamamos al dissector principal
    rftp.dissector(buffer, pinfo, tree)
    return true
end

-- Registrar como dissector heurístico en UDP
rftp:register_heuristic("udp", dissect_rftp_heur)

local udp_table = DissectorTable.get("udp.port")
udp_table:add(9001, rftp)
udp_table:add(9002, rftp)
